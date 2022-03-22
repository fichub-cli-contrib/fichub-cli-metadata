# Copyright 2022 Arbaaz Laskar

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Metadata(Base):
    __tablename__ = "fichub_metadata"

    id = Column(Integer, primary_key=True)
    fichub_id = Column(String)
    title = Column(String)
    author = Column(String, index=True)
    chapters = Column(Integer)
    created = Column(String)
    description = Column(String)
    rated = Column(String)
    language = Column(String)
    genre = Column(String)
    characters = Column(String)
    reviews = Column(Integer)
    favs = Column(Integer)
    follows = Column(Integer)
    status = Column(String)
    words = Column(Integer)
    fic_last_updated = Column(String)
    db_last_updated = Column(String)
    source = Column(String)
