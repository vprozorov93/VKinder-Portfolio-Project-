import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from VKinder.VKinder_database import database_settings

Base = declarative_base()


class UserSearchSettings(Base):
    __tablename__ = 'user_search_settings'

    vk_user = sql.Column(sql.Integer, primary_key=True)
    bdate = sql.Column(sql.Integer, nullable=True)
    sex = sql.Column(sql.Integer, nullable=True)
    city = sql.Column(sql.Text, nullable=True)
    relation = sql.Column(sql.Integer, nullable=True)

    likes = relationship('LikeTable', back_populates='user')
    dislikes = relationship('DislikeTable', back_populates='user')
    matches = relationship('MatchTable', back_populates='user')


class LikeTable(Base):
    __tablename__ = 'like_table'

    id = sql.Column(sql.Integer, primary_key=True)
    vk_user = sql.Column(sql.Integer, sql.ForeignKey('user_search_settings.vk_user'), nullable=False)
    like_user = sql.Column(sql.Integer, nullable=False)

    user = relationship(UserSearchSettings)


class DislikeTable(Base):
    __tablename__ = 'dislike_table'

    id = sql.Column(sql.Integer, primary_key=True)
    vk_user = sql.Column(sql.Integer, sql.ForeignKey('user_search_settings.vk_user'), nullable=False)
    dislike_user = sql.Column(sql.Integer, nullable=False)

    user = relationship(UserSearchSettings)


class MatchTable(Base):
    __tablename__ = 'match_table'

    id = sql.Column(sql.Integer, primary_key=True)
    vk_user1 = sql.Column(sql.Integer, sql.ForeignKey('user_search_settings.vk_user'), nullable=False)
    vk_user2 = sql.Column(sql.Integer, nullable=False)

    user = relationship(UserSearchSettings)


class DB:

    def __init__(self):
        db = f'postgresql://{database_settings.db_admin_name}:{database_settings.db_admin_password}@' \
             f'{database_settings.hostname}:{database_settings.port}/{database_settings.db_name}'
        self.engine = sql.create_engine(db, pool_size=50, max_overflow=0)
        self.Session = sessionmaker(bind=self.engine)

    def get_data(self, table: [UserSearchSettings, LikeTable, DislikeTable, MatchTable]):
        session = self.Session()
        data = session.query(table).all()
        session.close()
        return data

    def update_settings(self, vk_user: int, param: str, value: [int, str]):
        session = self.Session()
        session.query(UserSearchSettings).filter(UserSearchSettings.vk_user == vk_user).update({param: value})
        session.commit()
        session.close()

    def get_user_settings(self, vk_user: int):
        session = self.Session()
        data = session.query(UserSearchSettings).filter(UserSearchSettings.vk_user == vk_user).first()
        session.close()
        return data

    def get_like_user(self, vk_user: int, like_user: int):
        session = self.Session()
        data = (session.query(LikeTable).filter(LikeTable.vk_user == vk_user).filter(LikeTable.like_user == like_user).
                first())
        session.close()
        return data

    def get_dislike_user(self, vk_user: int, dislike_user: int):
        session = self.Session()
        data = (session.query(DislikeTable).filter(DislikeTable.vk_user == vk_user).
                filter(DislikeTable.dislike_user == dislike_user).first())
        session.close()
        return data

    def get_matches(self, vk_user: int):
        session = self.Session()
        return session.query(MatchTable).filter(MatchTable.vk_user1 == vk_user).all()

    def check_matches(self, vk_user: int, match_user: int):
        session = self.Session()
        data = session.query(MatchTable).filter(MatchTable.vk_user1 == vk_user). \
            filter(MatchTable.vk_user2 == match_user).first()
        session.close()
        return data

    def like_move_to_match(self, vk_user: int, like_user: int):
        session = self.Session()
        q1 = session.query(LikeTable).filter(LikeTable.vk_user == vk_user).filter(
            LikeTable.like_user == like_user).first()
        q2 = session.query(LikeTable).filter(LikeTable.vk_user == like_user).filter(
            LikeTable.like_user == vk_user).first()

        if q1 and q2:
            session.query(LikeTable).filter(LikeTable.vk_user == vk_user).filter(
                LikeTable.like_user == like_user).delete()
            session.query(LikeTable).filter(LikeTable.vk_user == like_user).filter(
                LikeTable.like_user == vk_user).delete()
            session.commit()
            match1 = MatchTable(vk_user1=vk_user, vk_user2=like_user)
            match2 = MatchTable(vk_user1=like_user, vk_user2=vk_user)
            self.write_to_db(match1)
            self.write_to_db(match2)

        session.close()

    def write_to_db(self, table: [UserSearchSettings, LikeTable, DislikeTable, MatchTable]):
        session = self.Session()
        session.add(table)
        session.commit()
        session.close()
