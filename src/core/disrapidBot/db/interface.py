from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker
import logging
import sys
from . import Base, migrate
from .guild import Guild, Channel, Role, Welcomemessage


class DisrapidDb:

    def __init__(self, *args, **kwargs):
        try:
            self.engine = create_engine('mysql+pymysql://' +
                                        f'{kwargs.pop("user")}:' +
                                        f'{kwargs.pop("passwd")}@' +
                                        f'{kwargs.pop("host")}' +
                                        ':3306/' +
                                        f'{kwargs.pop("name")}')

            self.Session = sessionmaker(bind=self.engine)

            Base.metadata.create_all(self.engine)
        except Exception as e:
            logging.fatal(e)
            sys.exit(1)

    def get_active_welcomemessage(self, session, guild_id):
        # this will just load the active welcome message
        try:
            return session.query(Welcomemessage) \
                                .filter(Welcomemessage.guild_id ==
                                        guild_id, Welcomemessage.enable
                                        == 1) \
                                .one()
        except Exception as e:
            logging.debug(e)
            return None

    def get_schema_version(self, session):
        # this will get the current database schema version
        try:
            return session.query(migrate.Schema).one()
        except Exception as e:
            logging.warning(e)
            return None

    def sync_guild(self, session, guild_id, name):
        # this function will synchronize a guild with the database
        #
        try:
            if session.query(exists()
                             .where(Guild.id == guild_id)) \
                             .scalar():
                # check / update the guild name
                session.query(Guild) \
                    .filter(Guild.id == guild_id,
                            Guild.name != name) \
                    .update({Guild.name: name})
            else:
                new_guild = Guild(id=guild_id)
                session.add(new_guild)

            session.commit()

        except Exception as e:
            logging.error(e)
            session.rollback()

    def del_guild(self, session, guild_id):
        # this function will delete a guild from the database
        #
        try:
            guild = session.query(Guild).get(guild_id)
            session.delete(guild)
            session.commit()
        except Exception as e:
            logging.error(f"unable to delete guild-{guild_id} reason: {e}")

    def sync_channel(self, session, guild_id, channel_id, name, channeltype):
        # this function will synchronize a channel with the database
        #
        try:
            if session.query(exists()
                             .where(Channel.id == channel_id)) \
                             .scalar():
                # check / update the channel name
                session.query(Channel) \
                    .filter(Channel.id == channel_id,
                            Channel.name != name) \
                    .update({Channel.name: name,
                             Channel.channeltype: channeltype.name})
            else:
                new_channel = Channel(id=channel_id,
                                      guild_id=guild_id,
                                      name=name,
                                      channeltype=channeltype.name)
                session.add(new_channel)

            session.commit()

        except Exception as e:
            logging.error(e)
            session.rollback()

    def sync_role(self, session, guild_id, role_id, name):
        # this function will synchronize a role with the database
        #
        try:
            if session.query(exists()
                             .where(Role.id == role_id)) \
                             .scalar():
                # check / update the role name
                session.query(Role) \
                    .filter(Role.id == role_id,
                            Role.name != name) \
                    .update({Role.name: name})
            else:
                new_role = Role(id=role_id,
                                guild_id=guild_id,
                                name=name)
                session.add(new_role)

            session.commit()

        except Exception as e:
            logging.error(e)
            session.rollback()
