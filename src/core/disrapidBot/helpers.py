from googleapiclient.discovery import build
import logging


class YouTubeHelper():
    def __init__(self, developer_key):
        self._developer_key = developer_key
        self._api = build('youtube', 'v3', developerKey=self._developer_key)

    def get_latest_activities(self, ytchannel_id):
        try:
            response = self._api.activities().list(
                part='snippet,contentDetails',
                channelId=ytchannel_id,
            ).execute()

            if 'error' in response:
                # this channel is invalid, we need to log
                return None

            if response['items'] == []:
                # this channel has no activities, return None
                return None

            items = []
            for item in response['items']:
                items.append(
                    YouTubeHelper._serialize_activity(
                        item
                    )
                )

            return items

        except Exception as e:
            logging.error(f"error in youtube api call: {e}")
            return False

    def get_channel_information(self, ytchannel_id):
        # this will respond channel information for 1 channel
        try:
            response = self._api.channels().list(
                part='statistics,snippet',
                id=ytchannel_id,
            ).execute()

            if 'error' in response:
                return False

            if 'items' in response:
                # serialize the first item of the response in a channel obj
                return YouTubeHelper._serialize_channel(
                    ytchannel_id,
                    response["items"][0]
                )

            else:
                return False

        except Exception as e:
            logging.error(f"error in youtube api call: {e}")
            return False

    @staticmethod
    def _serialize_activity(item):
        # serialize yt api response to an obj
        try:
            cd = item["contentDetails"]
            snip = item["snippet"]

            ytchannel = YouTubeActivity(
                id=cd["upload"]["videoId"],
                type=snip["type"],
                title=snip["title"],
                description=snip["description"],
            )

            return ytchannel
        except Exception as e:
            logging.error(f"error in youtube api channel serialization: {e}")
            return False

    @staticmethod
    def _serialize_channel(ytchannel_id, item):
        # serialize yt api response to an obj
        try:
            stat = item["statistics"]
            snip = item["snippet"]

            ytchannel = YouTubeChannel(
                id=ytchannel_id,
                title=snip["title"],
                description=snip["description"],
                publishedAt=snip["publishedAt"],
                subscriberCount=stat["subscriberCount"],
                hiddenSubscriberCount=stat["hiddenSubscriberCount"],
                viewCount=stat["viewCount"],
                commentCount=stat["subscriberCount"],
                videoCount=stat["videoCount"],
            )

            return ytchannel
        except Exception as e:
            logging.error(f"error in youtube api channel serialization: {e}")
            return False


class YouTubeActivity():
    def __init__(self, *args, **kwargs):
        activity_id = kwargs.pop("id")
        self.id = activity_id
        self.type = kwargs.pop("type")
        self.title = kwargs.get("title")
        self.description = kwargs.get("description")
        self.url = f"https://youtu.be/{activity_id}"


class YouTubeChannel():
    def __init__(self, *args, **kwargs):
        channel_id = kwargs.pop("id")
        self.id = channel_id
        self.url = f"https://www.youtube.com/channel/{channel_id}"
        self.title = kwargs.pop("title")
        self.description = kwargs.pop("description")
        self.publishedAt = kwargs.pop("publishedAt")
        self.subscriberCount = kwargs.pop("subscriberCount")
        self.viewCount = kwargs.pop("viewCount")
        self.hiddenSubscriberCount = kwargs.pop("hiddenSubscriberCount")
        self.commentCount = kwargs.pop("commentCount")
        self.videoCount = kwargs.pop("videoCount")
