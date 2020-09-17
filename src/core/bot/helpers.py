from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import re


def is_number(inputstring):
    return bool(re.match("^[0-9]*$", inputstring))


def is_string(inputstring):
    return bool(re.match("^[A-z0-9]*$", inputstring))


def is_extended_string(inputstring):
    return bool(re.match("^[A-z0-9 .,\n&:'`´%$!;:-_]+", inputstring))


def is_role(inputstring):
    return bool(re.match("<@&([0-9])*>", inputstring))


def is_channel(inputstring):
    return bool(re.match("<#([0-9])*>", inputstring))


def get_role_id_from_string(inputstring):
    tmp = inputstring[3:]
    tmp2 = tmp[:-1]
    return tmp2


def get_channel_id_from_string(inputstring):
    tmp = inputstring[2:]
    tmp2 = tmp[:-1]
    return tmp2


def is_custom_emoji(inputstring):
    return bool(re.match("^<:[A-z]*:[0-9]*>$", inputstring))


def modu(intvalue):
    if intvalue == 0:
        return "[OFF]"
    else:
        return "ON"


class YouTubeHelper():
    def __init__(self, developer_key):
        self._developer_key = developer_key
        self._api = build('youtube', 'v3', developerKey=self._developer_key)

    def get_activities(self, ytchannel_id):
        # DEPRECATED!!!
        # this returns all activity ids with quota cost 1
        try:
            r = self._api.activities().list(
                part='id',
                channelId=ytchannel_id
            ).execute()

            if r['items'] == []:
                return None

            items = []

            for item in r['items']:
                items.append(
                    item['id']
                )

            return items

        except HttpError as e:
            logging.error(
                "YouTubeHelper:get_activities: " +
                f"HttpError={e}"
            )
            return None
        except Exception as e:
            logging.error(
                "YouTubeHelper:get_activities: " +
                f"Exception={e}"
            )
            return None

    def get_activities_detailed(self, ytchannel_id):
        # this returns all activity ids with quota cost 3
        try:
            r = self._api.activities().list(
                part='id,contentDetails',
                channelId=ytchannel_id
            ).execute()

            if r['items'] == []:
                return None

            items = []

            for item in r['items']:
                if 'upload' in item['contentDetails']:
                    items.append(
                        {
                            "id": item['contentDetails']['upload']['videoId'],
                            "type": "upload",
                            "url": "https://youtu.be/" +
                            item['contentDetails']['upload']['videoId']
                        }
                    )

            return items

        except HttpError as e:
            logging.error(
                "YouTubeHelper:get_activities_detailed: " +
                f"HttpError={e}"
            )
            return None
        except Exception as e:
            logging.error(
                "YouTubeHelper:get_activities_detailed: " +
                f"Exception={e}"
            )
            return None

    def get_latest_activities(self, ytchannel_id):
        try:
            response = self._api.activities().list(
                part='snippet,contentDetails',
                channelId=ytchannel_id,
                uploadType="upload"
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
            logging.debug(
                f"_serialize_activity: item={item}"
            )

            cd = item["contentDetails"]
            snip = item["snippet"]

            logging.debug(
                f"_serialize_activity: cd={cd}, snip={snip}"
            )

            ytchannel = YouTubeActivity(
                id=cd["upload"]["videoId"],
                type=snip["type"],
                title=snip["title"],
                description=snip["description"],
            )

            logging.debug(
                f"_serialize_activity: ytchannel={ytchannel}"
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
