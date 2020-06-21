import logging
from discord.ext import commands, tasks
from db.youtube import Youtube, Activity, Goals
from db.guild import Guild, YoutubeFollow
from datetime import datetime
import random
from sqlalchemy import exists


class YoutubeAPI(commands.Cog, name="Youtube API"):
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

            s = self.db.Session()
            ytchannels = s.query(Youtube) \
                .filter(Youtube.valid == 1).all()

            if ytchannels is None:
                # there are no yt channels at all configured,
                # skip look
                logging.info("no yt channels to follow, skip loop")
                return

            # check all yt channels, if a new goal was reached
            for ytchannel in ytchannels:
                # query channel statistics
                ytc = self.bot.youtube \
                    .get_channel_information(ytchannel.ytchannel_id)

                # get the current goal values that refers to
                # current subscribercount from db
                goalval = s.query(Goals) \
                    .filter(ytc.subscriberCount >= Goals.min,
                            ytc.subscriberCount <= Goals.max).one()

                if goalval is None:
                    # something went wrong when trying to get
                    # current goal, report error an continue loop
                    pass

                if ytchannel.last_goal is None:
                    # we didn't checked the goal value for this yt
                    # channel before, check it and exit loop
                    s.query(Youtube) \
                        .filter(
                            Youtube.id == ytchannel.id
                        ) \
                        .update({
                            Youtube.last_goal: goalval.id,
                            Youtube.last_seen: datetime.now(),
                        })
                else:

                    # compare if goalval is greater than last goal
                    if goalval.id > ytchannel.last_goal:
                        # channel has reached a new subscriber goal!
                        # send a notification for all guilds that are
                        # following this channel and update last goal
                        s.query(Youtube) \
                            .filter(
                                Youtube.id == ytchannel.id
                            ) \
                            .update({
                                Youtube.last_goal: goalval.id,
                                Youtube.last_seen: datetime.now(),
                            })

                        # get all guilds that are following this yt
                        # channel and want to be notified about goals
                        for result in s.query(Guild, YoutubeFollow) \
                            .filter(
                                YoutubeFollow.guild_id == Guild.id,
                                YoutubeFollow.youtube_id == ytchannel.id,
                                YoutubeFollow.monitor_goals == 1,
                                ).all():

                            # get the channel id where notification should
                            # be sent to
                            nc = result.Guild.notify_channel_id

                            if nc is None:
                                # if no notification channel is set, send
                                # this to the guilds system channel
                                c = self.bot.get_guild(result.Guild.id) \
                                    .system_channel
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
                        s.query(Youtube) \
                            .filter(
                                Youtube.id == ytchannel.id
                            ) \
                            .update({Youtube.last_seen: datetime.now()})

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
            ytchannels = s.query(Youtube) \
                .filter(Youtube.valid == 1)

            if ytchannels is None:
                # there are no yt channels at all configured,
                # skip look
                logging.info("no yt channels to follow, skip loop")
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
                            new_activity = Activity(
                                id=a.id,
                                youtube_id=ytchannel.id,
                                last_sequence=seq
                            )
                            s.add(new_activity)
                        else:
                            # check if we already have seen this activity

                            if s.query(exists().where(Activity.id == a.id)) \
                                    .scalar():
                                # we have already seen this activity, update
                                # sequence id
                                s.query(Activity) \
                                    .filter(
                                        Activity.id == a.id
                                    ) \
                                    .update({Activity.last_sequence: seq})
                            else:
                                # this seems to be a new activity,
                                # execute notification procedure
                                new_activity = Activity(
                                    id=a.id,
                                    youtube_id=ytchannel.id,
                                    last_sequence=seq
                                )
                                s.add(new_activity)

                                # we need to notify all guilds, that are
                                # following this youtube channel about this
                                # new activity!
                                for result in s.query(Guild, YoutubeFollow) \
                                    .filter(
                                        YoutubeFollow.guild_id == Guild.id,
                                        YoutubeFollow.youtube_id ==
                                        ytchannel.id,
                                        YoutubeFollow.monitor_videos == 1,
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
                            s.query(Youtube) \
                                .filter(
                                    Youtube.id == ytchannel.id
                                ) \
                                .update({Youtube.last_seen: datetime.now()})

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


def setup(bot):
    bot.add_cog(YoutubeAPI(bot))
