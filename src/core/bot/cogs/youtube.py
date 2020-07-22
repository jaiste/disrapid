import logging
from discord.ext import commands, tasks
from datetime import datetime
import random
import models
from sqlalchemy import exists, and_
from helpers import is_string


class Youtube(commands.Cog, name="Youtube"):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.notify_yt_goals.start()
        self.notify_yt_act.start()

    @tasks.loop(minutes=0.3)
    async def notify_yt_goals(self):
        # this will check all followed yt channels and check if a goal
        # was reached ->
        # if so, we need to notify all guilds that are following this
        # yt channel
        # ...
        try:
            start_time = datetime.now()

            seq = random.getrandbits(32)  # generate sequence id
            logging.debug(f"starting new sequence notify_yt_goals-{seq}")

            s = self.db.Session()
            ytchannels = s.query(models.Youtube) \
                .filter(models.Youtube.valid == 1).all()

            if ytchannels is None:
                # if there are no yt channels at all configured, skip loop
                logging.debug(f"notify_yt_goals-{seq} no yt channels to " +
                              "follow, skipping loop")
                return

            # check all yt channels, if a new goal was reached
            for ytchannel in ytchannels:
                logging.debug(f"notify_yt_goals-{seq} checking channel-" +
                              f"{ytchannel.ytchannel_id} current stats")
                # query channel statistics from YT API
                ytc = self.bot.youtube \
                    .get_channel_information(ytchannel.ytchannel_id)

                logging.debug(f"notify_yt_goals-{seq} current goal=" +
                              f"{ytc.subscriberCount}")

                # get the current goal values that refers to
                # current subscribercount from db
                goalval = s.query(models.Goals) \
                    .filter(ytc.subscriberCount >= models.Goals.min,
                            ytc.subscriberCount <= models.Goals.max).one()

                if goalval is None:
                    # something went wrong when trying to get
                    # current goal, report error an continue loop
                    logging.error(f"notify_yt_goals-{seq} there was an " +
                                  "error in checking goals for channel-" +
                                  f"{ytchannel.ytchannel_id}")
                    pass

                if ytchannel.last_goal is None:
                    # we didn't checked the goal value for this yt
                    # channel before, check it and exit loop
                    logging.debug(
                        f"notify_yt_goals-{seq} channel-" +
                        f"{ytchannel.ytchannel_id} was never queried" +
                        "before, inserting values in database")

                    s.query(models.Youtube) \
                        .filter(
                            models.Youtube.id == ytchannel.id
                        ) \
                        .update({
                            models.Youtube.last_goal: goalval.id,
                            models.Youtube.last_seen: datetime.now(),
                        })

                else:

                    # compare if goalval is greater than last goal
                    if goalval.id > ytchannel.last_goal:
                        # channel has reached a new subscriber goal!
                        # send a notification for all guilds that are
                        # following this channel and update last goal
                        logging.debug(f"notify_yt_goals-{seq} channel-" +
                                      f"{ytchannel.ytchannel_id} has rea" +
                                      "ched a new goal! notifying guilds")

                        s.query(models.Youtube) \
                            .filter(
                                models.Youtube.id == ytchannel.id
                            ) \
                            .update({
                                models.Youtube.last_goal: goalval.id,
                                models.Youtube.last_seen: datetime.now(),
                            })

                        # get all guilds that are following this yt
                        # channel and want to be notified about goals
                        for result in s.query(
                                models.Guild,
                                models.YoutubeFollow
                            ) \
                            .filter(
                                models.YoutubeFollow.guild_id ==
                                models.Guild.id,
                                models.YoutubeFollow.youtube_id ==
                                ytchannel.id,
                                models.YoutubeFollow.monitor_goals == 1,
                                ).all():

                            # get the channel id where notification should
                            # be sent to
                            nc = result.Guild.notify_channel_id

                            if nc is None:
                                # if no notification channel is set, send
                                # this to the guilds system channel
                                c = self.bot.get_guild(
                                    result.Guild.id
                                    ).system_channel
                            else:
                                c = self.bot.get_channel(nc)

                            # replace $channelname by real channelname
                            if goalval.text is not None:
                                msg = goalval.text.replace(
                                    "$channelname",
                                    ytc.title,
                                )
                                msg += "\nCheckout this channel:"
                                msg += f" {ytc.url}"

                                # send a notification to the channel
                                await c.send(msg)
                            else:
                                logging.error("taskloop error: goalval" +
                                              ".text is empty, " +
                                              "what shouldn't happen!")

                    else:
                        # nothing has changed for this channel, update
                        # last seen value in db an continue loop
                        logging.debug(
                            f"notify_yt_goals-{seq} channel-" +
                            f"{ytchannel.ytchannel_id} as not change" +
                            "d it's last goal, updating last seen"
                        )

                        s.query(models.Youtube) \
                            .filter(
                                models.Youtube.id == ytchannel.id
                            ) \
                            .update({models.Youtube.last_seen: datetime.now()})

            s.commit()
            s.close()

            run_time = datetime.now() - start_time
            logging.info(f"telemetry: notify_yt_goals took {run_time}s")

        except Exception as e:
            run_time = datetime.now() - start_time
            logging.error(
                f"notify_yt_goals failed because of: {e} {run_time}s"
            )
            s.rollback()
            s.close()

    @notify_yt_goals.before_loop
    async def before_yt_goals(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=0.3)
    async def notify_yt_act(self):
        # this will notify about new activites on a yt channel
        # ->
        # notify all guilds that are following this yt channel
        #
        try:
            start_time = datetime.now()

            seq = random.getrandbits(32)  # generate sequence id

            s = self.db.Session()

            # get all youtube channels we need to follow
            ytchannels = s.query(models.Youtube) \
                .filter(models.Youtube.valid == 1)

            if ytchannels is None:
                # there are no yt channels at all configured,
                # skip look
                logging.debug(f"notify_yt_goals-{seq} no yt channels to " +
                              "follow, skipping loop")
                return

            # check all yt channels, if there is a new activity
            for ytchannel in ytchannels:
                # query channel statistics
                yta = self.bot.youtube \
                    .get_latest_activities(ytchannel.ytchannel_id)

                if yta is not False and yta:
                    for a in yta:
                        # do that for all activities...
                        if ytchannel.last_seen is None:
                            # insert activity in database and do nothing...
                            new_activity = models.Activity(
                                id=a.id,
                                youtube_id=ytchannel.id,
                                last_sequence=seq
                            )
                            s.add(new_activity)
                        else:
                            # check if we already have seen this activity

                            if s.query(
                                exists()
                                .where(
                                    models.Activity.id == a.id
                                )) \
                                    .scalar():
                                # we have already seen this activity, update
                                # sequence id
                                s.query(models.Activity) \
                                    .filter(
                                        models.Activity.id == a.id
                                    ) \
                                    .update(
                                        {models.Activity.last_sequence: seq}
                                    )
                            else:
                                # this seems to be a new activity,
                                # execute notification procedure
                                new_activity = models.Activity(
                                    id=a.id,
                                    youtube_id=ytchannel.id,
                                    last_sequence=seq
                                )
                                s.add(new_activity)

                                # we need to notify all guilds, that are
                                # following this youtube channel about this
                                # new activity!
                                for result in s.query(
                                            models.Guild,
                                            models.YoutubeFollow
                                        ) \
                                    .filter(
                                        models.YoutubeFollow.guild_id ==
                                        models.Guild.id,
                                        models.YoutubeFollow.youtube_id ==
                                        ytchannel.id,
                                        models.YoutubeFollow.monitor_videos ==
                                        1,
                                        ).all():

                                    # get the channel id where notification
                                    # should be sent to
                                    nc = result.Guild.notify_channel_id

                                    if nc is None:
                                        # if no notification channel is set,
                                        # send
                                        # this to the guilds system channel
                                        c = self.bot.get_guild(
                                            result.Guild.id
                                        ).system_channel
                                    else:
                                        c = self.bot.get_channel(nc)

                                    await c.send(a.url)

                            # clean up task
                            s.query(models.Youtube) \
                                .filter(
                                    models.Youtube.id == ytchannel.id
                                ) \
                                .update({
                                    models.Youtube.last_seen: datetime.now()
                                })

            s.commit()
            s.close()

            run_time = datetime.now() - start_time
            logging.info(f"telemetry: notify_yt_act took {run_time}s")

        except Exception as e:
            run_time = datetime.now() - start_time
            logging.error(f"notify_yt_act failed because of: {e} {run_time}s")
            s.rollback()
            s.close()

    @notify_yt_act.before_loop
    async def before_yt_act(self):
        await self.bot.wait_until_ready()

    # ADMIN CONFIG COMMANDS
    # ---
    #
    @commands.has_permissions(administrator=True)
    @commands.group()
    async def youtube(self, ctx):
        if ctx.invoked_subcommand is None:
            # await ctx.send("No subcommand posted")
            pass

    @youtube.command()
    async def add(self, ctx, ytchannel_id: str):
        # this will add the yt channel to followinglist
        if not is_string(ytchannel_id):
            return

        s = self.db.Session()

        # check if channel is already existing in database
        yt_id = self._get_yt_id(s, ytchannel_id)

        if yt_id is not None:
            # channel is existing, check if channel is on followlist
            if self._exists_ytfollow(s, yt_id, ctx.guild.id):
                # is already on list, send message
                await ctx.send(
                    "This channel is already on your followinglist"
                )
            else:
                # channel is not existing, add to list
                new_ytf = models.YoutubeFollow(
                    guild_id=ctx.guild.id,
                    youtube_id=yt_id,
                    monitor_videos=0,
                    monitor_goals=0,
                    monitor_streams=0,
                    remind_streams=0
                )
                s.add(new_ytf)
                s.commit()

                await ctx.send(
                    "Channel was added to your followinglist"
                )

        else:
            # channel is not existing, add to the database

            # check if the channel is a valid youtube channel
            # WIP!
            #

            new_yt = models.Youtube(
                valid=True,
                ytchannel_id=ytchannel_id
            )
            s.add(new_yt)
            s.commit()

            yt_id = self._get_yt_id(s, ytchannel_id)

            new_ytf = models.YoutubeFollow(
                guild_id=ctx.guild.id,
                youtube_id=yt_id,
                monitor_videos=0,
                monitor_goals=0,
                monitor_streams=0,
                remind_streams=0,
            )
            s.add(new_ytf)
            s.commit()

            await ctx.send(
                "Channel was added to your followinglist"
            )

        s.close()

    @youtube.command()
    async def rm(self, ctx, ytchannel_id: str):
        # this will remove the yt channel from followinglist
        if not is_string(ytchannel_id):
            return

        s = self.db.Session()

        yt_id = self._get_yt_id(s, ytchannel_id)

        if yt_id is None:
            await ctx.send(
                "Channel is not on your followinglist"
            )
            return

        # check if this is on followinglist
        if self._exists_ytfollow(s, yt_id, ctx.guild.id):
            # is on the guilds followinglist remove it
            ytf = s.query(
                models.YoutubeFollow
            ).filter(
                models.YoutubeFollow.youtube_id == yt_id,
                models.YoutubeFollow.guild_id == ctx.guild.id
            ).one()

            s.delete(ytf)

            # check if this is the last guild, remove it from yt
            if not s.query(
                exists()
                .where(
                    models.YoutubeFollow.youtube_id == yt_id
                    )).scalar():
                ytc = s.query(
                    models.Youtube
                ).get(yt_id)

                s.delete(ytc)

            s.commit()

            await ctx.send(
                "Channel was removed from your followinglist"
            )

        else:
            await ctx.send(
                "Channel is not on your followinglist"
            )

        s.close()

    @youtube.command()
    async def show(self, ctx, ytchannel_id: str):
        # this will print the current channel configuration
        pass

        # check if channel id is on followinglist
        #   yes:
        #       print current config
        #   no: respond

    @youtube.command()
    async def enable_goal_notify(self, ctx, ytchannel_id: str):
        # this will enable the goal notification for the yt channel
        pass

    @youtube.command()
    async def disable_goal_notify(self, ctx, ytchannel_id: str):
        # this will disable the goal notification for the yt channel
        pass

    # @youtube.command()
    # async def enable_stream_notify(self, ctx, ytchannel_id: str):
    #     # this will enable the stream notification for the yt channel
    #     pass

    # @youtube.command()
    # async def disable_stream_notify(self, ctx, ytchannel_id: str):
    #     # this will disable the stream notification for the yt channel
    #     pass

    # @youtube.command()
    # async def enable_stream_reminder(self, ctx, ytchannel_id: str):
    #     # this will enable the stream reminder for the yt channel
    #     pass

    # @youtube.command()
    # async def disable_stream_reminder(self, ctx, ytchannel_id: str):
    #     # this will disable the stream reminder for the yt channel
    #     pass

    @youtube.command()
    async def enable_upload_notify(self, ctx, ytchannel_id: str):
        # this will enable the upload notification for the yt channel
        pass

    @youtube.command()
    async def disable_upload_notify(self, ctx, ytchannel_id: str):
        # this will disable the upload notification for the yt channel
        pass

    # add staticmethod when channel on following list
    # ...

    def _get_yt_id(self, s, ytchannel_id):
        # this will return a yt_id of a youtubechannel if existing in
        # our database
        # ---
        #
        try:
            if s.query(
                exists()
                .where(
                    models.Youtube.ytchannel_id == ytchannel_id
                )
            ).scalar():
                # get channel id
                yt_id = s.query(
                    models.Youtube
                ).filter(
                    models.Youtube.ytchannel_id == ytchannel_id
                ).one()

                return yt_id.id
            else:
                return None
        except Exception as e:
            logging.error(
                f"error in _ytchannel_existing: {e}"
            )
            return None

    def _exists_ytfollow(self, s, yt_id, guild_id):
        # this return true when yt channel is followed for guild
        # ---
        #
        try:

            if s.query(
                exists().
                where(
                    and_(
                        models.YoutubeFollow.youtube_id == yt_id,
                        models.YoutubeFollow.guild_id == guild_id
                    )
                )
            ).scalar():
                return True
        except Exception as e:
            logging.error(
                f"error in _exists_ytfollow: {e}"
            )
            return False


def setup(bot):
    bot.add_cog(Youtube(bot))
