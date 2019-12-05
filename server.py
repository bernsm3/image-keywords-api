from datetime import datetime
from flask import *
from dataclasses import dataclass, field

app = Flask(__name__)

# store user credentials
restricted_users = {
    'rootuser':'rootpass'
}

normal_users = {
    'user1':'pass1'
}
normal_users.update(restricted_users)

# store data
input = {
    'Character' : [
        'Batman',
        'Kurt Cobain',
        'Teacher',
        'Doctor'
    ],
    'Subject' : [
        'Military',
        'Climate Change',
        'Food',
        'Queen Mary',
        'Gaming'
    ],
    'Setting' : [
        'Kitchen',
        'Hospital',
        'Desert',
        'Barn',
        'College',
        'Stalingrad'
    ],
    'Theme' : [
        'Growing up',
        'Underdog',
        'Transformation',
        'Love',
        'Adventure'
    ],
    'Mood' : [
        'Gory',
        'Thrilling',
        'Gloomy',
        'Ecstatic',
        'Melancholy',
        'Patriotic'
    ]
}

# this could be done more robustly with pd.MultiIndex (not to mention a real database)
# WARNING: error handling takes place within the API methods, there is no error
# handling here; internal use only.
@dataclass
class Category:
    name       : str
    user_added : str      = '<default>'
    date_added : datetime = datetime.now()
    keywords   : dict     = field(default_factory=dict)

@dataclass
class Keyword:
    name       : str
    user_added : str      = '<default>'
    date_added : datetime = datetime.now()
    deprecated : bool     = False

@dataclass
class Record:
    keyword      : Keyword
    user_changed : str      = '<default>'
    date_changed : datetime = datetime.now()
    def __post_init__(self):
        self.name  = self.getKeywordName()
    def getKeywordName(self):
        try:
            return self.keyword.name
        except AttributeError:
            return None

#Image.history is a Dict[Category.name,List[Record]]
@dataclass
class Image:
    id         : str
    user_added : str      = '<default>'
    date_added : datetime = datetime.now()
    history    : dict     = field(default_factory=dict)

    def get_keyword(self, category_name):
        try:
            kw = self.history[category_name][-1].keyword
            if not kw.deprecated:
                return kw
        except AttributeError:
            return None
    def get_current_keywords(self):
        return { cat:self.get_keyword(cat) for cat in self.history.keys() }

    def add_keyword(self, category_name, keyword, user='<default>', date=datetime.now()):
        self.history[category_name].append(Record(keyword,user,date))

categories = {
    key:Category(key,
        keywords={v:Keyword(v) for v in val}
    ) for key,val in input.items()
}

images = {

    '00000000aaaaaaaa':Image('00000000aaaaaaaa',
        history={
            'Character':[
                Record(categories['Character'].keywords['Batman'])
            ],
            'Subject':[
                Record(None)
            ],
            'Setting':[
                Record(None)
            ],
            'Theme':[
                Record(categories['Theme'].keywords['Adventure']),
                Record(categories['Theme'].keywords['Love'])
            ],
            'Mood':[
                Record(None)
            ]
        }
    ),

    '00000000bbbbbbbb':Image('00000000bbbbbbbb',
        history={
            'Character':[
                Record(None)
            ],
            'Subject':[
                Record(None)
            ],
            'Setting':[
                Record(None)
            ],
            'Theme':[
                Record(None)
            ],
            'Mood':[
                Record(None)
            ]
        }
    )
}

fake_database = {
    'restricted_users' : restricted_users,
    'normal_users'     : normal_users,
    'categories'       : categories,
    'images'           : images
}

##### Image API #####

@app.route('/images/', methods = ['GET'])
def get_images():
    return jsonify( {im.name:im.get_current_keywords() for im in fake_database['images'].values()} )

@app.route('/images/<string:id>', methods = ['GET'])
def get_image(id):
    return jsonify( fake_database['images'][id].get_current_keywords() )

@app.route('/history/images/', methods = ['GET'])
def get_image_histories():
    return jsonify( fake_database['images'].values() )

@app.route('/history/images/<string:id>', methods = ['GET'])
def get_image_history(id):
    return jsonify( fake_database['images'][id] )

# post instead of put because it always has the side effect of creating a new
# record, even if the keyword is the same
@app.route('/images/<string:id>', methods = ['POST'])
def update_image_kw(id):
    image = fake_database['images'][id]
    cat_name = request.form['category']
    kw = fake_database['categories'][cat_name].keywords[request.form['keyword']]
    if kw.deprecated:
        kw = None
    image.add_keyword(cat_name, kw, date=request.date)
    return get_image(id)

# all images start with None as the keyword for each category; makes delete() return to the original state
@app.route('/images/<string:id>', methods = ['DELETE'])
def delete_image_kw(id):
    image = fake_database['images'][id]
    cat_name = request.form['category']
    image.add_keyword(cat_name, None, date=request.date)
    return get_image(id)

# images cannot be deleted
@app.route('/images/<string:id>', methods = ['PUT'])
def create_image(id):
    history = {}
    for cat_name in fake_database['categories'].keys():
        try:
            kw = fake_database['categories'][cat_name].keywords[request.form[cat_name]]
            if kw.deprecated:
                kw = None
        except KeyError:
            kw = None
        history[cat_name] = [Record(kw, date_changed=request.date)]
    fake_database['images'][id] = Image(id, date_added=request.date, history=history)
    return get_image(id)


##### Keyword API (restricted users only, besides GET) #####

@app.route('/keywords/', methods = ['GET'])
def get_categories():
    return jsonify( list(fake_database['categories'].keys()) )

@app.route('/keywords/<string:cat_name>', methods = ['GET'])
def get_keywords(cat_name):
    return jsonify( list(filter(lambda k: not k.deprecated,
                fake_database['categories'][cat_name].keywords.keys()))
            )

@app.route('/history/keywords/<string:cat_name>', methods = ['GET'])
def get_keyword_histories(cat_name):
    return jsonify( {kw.name:kw for kw in list(filter(lambda k: not k.deprecated,
                fake_database['categories'][cat_name].keywords.values()))}
            )

@app.route('/history/keywords/<string:cat_name>/<string:kw_name>', methods = ['GET'])
def get_keyword_history(cat_name,kw_name):
    if fake_database['categories'][cat_name].keywords[kw_name].deprecated:
        return jsonify({})
    return jsonify( { kw_name:kw } )

# warning: expensive (loop over images)
@app.route('/keywords/<string:cat_name>', methods = ['PUT'])
def create_category(cat_name):
    try:
        fake_database['categories'][cat_name]
    except KeyError:
        fake_database['categories'][cat_name] = Category(cat_name,date_created=request.date)
        for im in fake_database['images']:
            im.history[cat_name] = [Record(None, date_changed=request.date)]
    return get_keyword_histories(cat_name)

@app.route('/keywords/<string:cat_name>/<string:kw_name>', methods = ['PUT'])
def create_keyword(cat_name,kw_name):
    try:
        fake_database['categories'][cat_name][kw_name].deprecated = False
    except KeyError:
        fake_database['categories'][cat_name][kw_name] = Keyword(kw_name,date_created=request.date)
    return get_keyword_history(cat_name,kw_name)

# warning: expensive (loop over images),irreversible (deletes associated histories)
@app.route('/keywords/<string:cat_name>', methods = ['DELETE'])
def delete_category(cat_name):
    for im in fake_database['images']:
        im.history.pop(cat_name, None)
    fake_database['categories'].pop(cat_name, None)
    return get_categories()

# soft delete
@app.route('/keywords/<string:cat_name>/<string:kw_name>', methods = ['DELETE'])
def delete_keyword(cat_name,kw_name):
    try:
        fake_database['categories'][cat_name][kw_name].deprecated = True
    except KeyError:
        pass
    return get_keywords(cat_name)
