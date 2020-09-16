import logging
from discord.ext import commands, tasks
from datetime import datetime
import random
import models
from sqlalchemy import exists, and_
from helpers import (
    is_string,
    is_role,
    get_role_id_from_string,
    is_channel,
    get_channel_id_from_string,
)
import os

if 'DEBUG' in os.environ:
    TASK_LOOP_TIME = 0.3
else:
    TASK_LOOP_TIME = 5


def ytmodf(intvalue):
    if intvalue == 0:
        return "[OFF]"
    else:
        return "ON"


class Youtube(commands.Cog, name="Youtube"):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.notify_yt_goals.start()
        self.notify_yt_act.start()

    # MAIN LOOP FUNCTIONS
    # ---
    #
    @tasks.loop(minutes=TASK_LOOP_TIME)
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

                            # get the role id that should be notified
                            if result.Guild.notify_role_id is not None:
                                role = self.bot.get_guild(
                                    result.Guild.id
                                ).get_role(
                                    result.Guild.notify_role_id
                                )
                            else:
                                role = None

                            # replace $channelname by real channelname
                            if goalval.text is not None:
                                msg = goalval.text.replace(
                                    "$channelname",
                                    ytc.title,
                                )
                                if role is not None:
                                    msg += role.mention

                                msg += "Checkout this channel:"
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

    @tasks.loop(minutes=TASK_LOOP_TIME)
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

            # query all activities for channel
            for ytchannel in ytchannels:
                # query channel statistics
                yta = self.bot.youtube \
                    .get_activities_detailed(ytchannel.ytchannel_id)

                # if we don't get any activities for any reason,
                # continue with the next channel ...
                if yta is None:
                    logging.error(
                        "notify_yt_act: " +
                        f"error for channel-{ytchannel.ytchannel_id}," +
                        "skipping this channel and move to next"
                    )

                    # update all activities with seq id + datetime
                    s.query(models.Activity) \
                        .filter(
                            models.Activity.youtube_id == ytchannel.id
                        ) \
                        .update({
                            models.Activity.last_sequence: seq
                        })

                    continue

                # check if we have queried this channel before
                if ytchannel.last_seen is None:
                    # we didn't query this channel before, insert
                    # everything in db and do nothing...
                    for a in yta:
                        new_activity = models.Activity(
                            id=a.get('id'),
                            youtube_id=ytchannel.id,
                            last_sequence=seq
                        )
                        s.add(new_activity)

                    s.commit()

                else:
                    # we have queried this channel before, check
                    # if the activities are in db
                    for a in yta:
                        if s.query(
                            exists()
                            .where(
                                models.Activity.id == a.get('id')
                                )).scalar():
                            # we have already seen this activity
                            # update seq id
                            s.query(models.Activity) \
                                .filter(
                                    models.Activity.id == a.get('id')
                                ) \
                                .update(
                                    {models.Activity.last_sequence: seq}
                                )
                        else:
                            # we have not seen this activity
                            # this is a new activity we need to
                            # send a notification for...
                            new_activity = models.Activity(
                                id=a.get('id'),
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

                                # get the role that should be notified
                                nr_id = result.Guild.notify_role_id
                                nr = self.bot.get_guild(
                                    result.Guild.id
                                ).get_role(
                                    nr_id
                                ).mention

                                if nc is None:
                                    # if no notification channel is set,
                                    # send
                                    # this to the guilds system channel
                                    c = self.bot.get_guild(
                                        result.Guild.id
                                    ).system_channel
                                else:
                                    c = self.bot.get_channel(nc)

                                # send notification message to channel
                                await c.send(
                                    f"Hey {nr}, there is a new youtube video: "
                                    f"{a.get('url')}"
                                )

                # clean up task
                s.query(models.Youtube) \
                    .filter(
                        models.Youtube.id == ytchannel.id
                    ) \
                    .update({
                        models.Youtube.last_seen: datetime.now()
                    })

                s.commit()

            # clean up orphaned entires
            oe = s.query(
                models.Activity
            ).filter(
                models.Activity.last_sequence != seq
            )
            oe.delete()

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
        if ctx.invoked_subcommand is not None:
            return

        try:
            s = self.db.Session()

            # ytchannels = []

            db_guild = s.query(models.Guild).get(ctx.guild.id)

            role = ctx.guild.get_role(db_guild.notify_role_id)
            channel = ctx.guild.get_channel(db_guild.notify_channel_id)

            if role is not None:
                role = role.mention
            else:
                "*None*"

            if channel is not None:
                channel = channel.mention
            else:
                "*None*"

            msg = "**YouTube Settings**\n---\n\n" \
                f"Notifications Channel: {channel}\n" \
                f"Notifications Role: {role}\n\n"

            msg += "Following List:\n---\n"
            msg += "```css\n"
            msg += "/* Syntax= .channel_id : (notify_videos),"
            msg += " (notify_goals) */\n\n"

            # get all youtube channels
            for result in s.query(
                    models.Youtube,
                    models.YoutubeFollow
                ) \
                .filter(
                    models.YoutubeFollow.guild_id ==
                    ctx.guild.id,
                    models.YoutubeFollow.youtube_id ==
                    models.Youtube.id
                    ).all():

                msg += f".{result.Youtube.ytchannel_id} : "
                msg += f"{ytmodf(result.YoutubeFollow.monitor_videos)}"
                msg += f", {ytmodf(result.YoutubeFollow.monitor_goals)}"
                msg += "\n"

            msg += "```"

            await ctx.send(msg)

            s.close()

        except Exception as e:
            logging.error(
                f"Error in youtube command: {e}"
            )
            s.rollback()
            s.close()

    @youtube.command()
    async def add(self, ctx, ytchannel_id: str):
        # this will add the yt channel to followinglist
        try:
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

        except Exception as e:
            logging.error(
                f"Error in youtube.add command: {e}"
            )
            s.rollback()
            s.close()

    @youtube.command()
    async def rm(self, ctx, ytchannel_id: str):
        # this will remove the yt channel from followinglist
        try:
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

        except Exception as e:
            logging.error(
                f"Error in youtube.rm command: {e}"
            )
            s.rollback()
            s.close()

    # @youtube.command()
    # async def show(self, ctx, ytchannel_id: str):
        # this will print the current channel configuration
        # pass

        # check if channel id is on followinglist
        #   yes:
        #       print current config
        #   no: respond

    @youtube.command()
    async def enable_goal_notify(self, ctx, ytchannel_id: str):
        # this will enable the goal notification for the yt channel
        if not is_string(ytchannel_id):
            return

        s = self.db.Session()
        self._switch_ytmod(
            s,
            ctx.guild.id,
            ytchannel_id,
            "monitor_goals",
            1
        )

        s.commit()

        await ctx.send(
            "Goal Notifications enabled for channel."
        )

        s.close()

    @youtube.command()
    async def disable_goal_notify(self, ctx, ytchannel_id: str):
        # this will disable the goal notification for the yt channel
        if not is_string(ytchannel_id):
            return

        s = self.db.Session()
        self._switch_ytmod(
            s,
            ctx.guild.id,
            ytchannel_id,
            "monitor_goals",
            0
        )

        s.commit()

        await ctx.send(
            "Goal Notifications disabled for channel."
        )

        s.close()

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
        if not is_string(ytchannel_id):
            return

        s = self.db.Session()
        self._switch_ytmod(
            s,
            ctx.guild.id,
            ytchannel_id,
            "monitor_videos",
            1
        )

        s.commit()

        await ctx.send(
            "Upload Notifications enabled for channel."
        )

        s.close()

    @youtube.command()
    async def disable_upload_notify(self, ctx, ytchannel_id: str):
        # this will disable the upload notification for the yt channel
        if not is_string(ytchannel_id):
            return

        s = self.db.Session()
        self._switch_ytmod(
            s,
            ctx.guild.id,
            ytchannel_id,
            "monitor_videos",
            0
        )

        s.commit()

        await ctx.send(
            "Upload Notifications disabled for channel."
        )

        s.close()

    @youtube.command()
    async def notify_role(self, ctx, role: str):
        # this will change the notification role
        try:
            s = self.db.Session()

            # check if user want's to remove the role
            if role.lower() == "none":
                s.query(models.Guild) \
                    .filter(
                        models.Guild.id == ctx.guild.id
                    ) \
                    .update({
                        models.Guild.notify_role_id: None
                    })
                s.commit()
                s.close()
                return

            if not is_role(role):
                await ctx.send(
                    "this is not a valid role argument, please use the @ "
                    "character to directly tag a discord role object..."
                )
                s.close()
                return

            # extract role id
            role_id = get_role_id_from_string(role)

            # skip if this role is not existing on the server
            if ctx.guild.get_role(int(role_id)) is None:
                await ctx.send(
                    "role is not existing on guild..."
                )
                s.close()
                return

            # update the db entry
            s.query(models.Guild) \
                .filter(
                    models.Guild.id == ctx.guild.id
                ) \
                .update({
                     models.Guild.notify_role_id: role_id
                })
            s.commit()

            await ctx.channel.send(
                "notification role was updated..."
            )

        except Exception as e:
            logging.error(
                f"Error in youtube notify role command: {e}"
            )
            s.close()

    @youtube.command()
    async def notify_channel(self, ctx, channel: str):
        # this will change the notification role
        try:
            s = self.db.Session()

            # check if user want's to remove the role
            if channel.lower() == "none":
                s.query(models.Guild) \
                    .filter(
                        models.Guild.id == ctx.guild.id
                    ) \
                    .update({
                        models.Guild.notify_channel_id: None
                    })
                s.commit()
                s.close()
                return

            if not is_channel(channel):
                await ctx.send(
                    "this is not a valid channel argument, please use the # "
                    "character to directly tag a discord channel object..."
                )
                s.close()
                return

            channel_id = get_channel_id_from_string(channel)  # extract id

            # error if channel is not existing on guild
            if ctx.guild.get_channel(int(channel_id)) is None:
                await ctx.send(
                    "channel is not existing on guild..."
                )
                s.close()
                return

            # update the db entry
            s.query(models.Guild) \
                .filter(
                    models.Guild.id == ctx.guild.id
                ) \
                .update({
                     models.Guild.notify_channel_id: channel_id
                })
            s.commit()

            await ctx.channel.send(
                "notification channel was updated..."
            )

        except Exception as e:
            logging.error(
                f"Error in youtube notify role command: {e}"
            )
            # s.close()

    # PRIVATE HELPER FUNCTIONS
    # ---
    #
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

    def _switch_ytmod(self, s, guild_id, ytchannel_id, mod, value):
        # this will switch a youtube module on a specific channel on/off
        # based on guild_id
        # ---
        #
        try:

            # get yt_id
            yt_id = self._get_yt_id(s, ytchannel_id)

            s.query(models.YoutubeFollow) \
                .filter(
                    models.YoutubeFollow.youtube_id == yt_id,
                    models.YoutubeFollow.guild_id == guild_id
                ) \
                .update({
                    getattr(models.YoutubeFollow, mod): value
                })

        except Exception as e:
            logging.error(
                f"error in _exists_ytfollow: {e}"
            )
            return False


def setup(bot):
    bot.add_cog(Youtube(bot))
