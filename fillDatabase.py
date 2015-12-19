from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, CatalogItem, User

engine = create_engine('sqlite:///itemscatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


#fake user
User1 = User(name="Roger Racoon", email="roger@racoons.com",
             picture="https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQJHRPOQuZkfzToz246TrwmCHhHMM-2MDgHnsYUdon-SuwC4BUa3pBP3x4")
session.add(User1)
session.commit()


#add categories

category1 = Category(user_id=1, name="Baseball")
session.add(category1)
session.commit()

#add items for Baseball
item1 = CatalogItem(name="Baseball Bat",
                    description="This is an object used to his the incoming ball. Made of an aloy compound designed to launch the ball on contact",
                    category_id=1,
                    user_id=1)
session.add(item1)
session.commit()

item2 = CatalogItem(name="Ball",
                    description="This is a ball used in the sport of baseball not to be confused with a basketball.",
                    category_id=1,
                    user_id=1)
session.add(item2)
session.commit()

category2 = Category(user_id=1, name="Hockey")
session.add(category2)
session.commit()

item3 = CatalogItem(name="Puck",
                 description="This object is comparable to a ball in other sports. It is a rubber cylinder that gets hit around the ice.",
                 category_id=2,
                 user_id=1)
session.add(item3)
session.commit()

print "Items catalog filled!"
