## Image Keywords API
A simple Flask REST API to manage image keywords.

### TL;DR
```
$ git clone https://github.com/bernsm3/image-keywords-api.git
$ cd image-keywords-api/
$ pip install -r requirements.txt
$ export FLASK_APP=server.py
$ python -m flask run
```
Request `http://localhost:5000/<endpoint>`; see `test.py` for usage examples or **API endpoints** for docs.

### Use case
There exist categories (`Character`, `Subject`, `Setting`...) of possible keywords (`Character`: `Batman`, `Kurt Cobain`...).

An image (16-character alphanumeric unique ID) has at most one keyword associated with it per category.

Users are logged in. Some have permission to create new categories or keywords. All have permission to edit image keywords.

Edit history by user must be tracked for each image.

Assumptions:
*  The number of possible keywords is very large
*  The number of categories, and therefore the number of keywords per image, is small
*  Keyword names are unique only within each category (`Character.Batman != Subject.Batman`)
*  Image-associated endpoints must be fast (frequently used).
*  Category- or keyword-associated endpoints don't have to be fast (infrequently used).
*  Because this API doesn't know what applications depend on its database, soft deletes only, just in case.
*  Images are arbitrarily old, so an image history can be large.

### Design choices
For the data representation, my first thought was to enforce type-safety on keywords belonging to different categories, as well as uniqueness of keywords and image IDs, by using `enum`s. But this wasn't workable with the conflicting requirements of having metadata (usernames) attached to keywords, so I decided to skip right past a pseudo-database using `pd.DataFrame` and `pd.MultiIndex` and committed to having both username and datetime metadata attached to images, keywords, and categories using an object-oriented design. `@dataclass` allowed these objects to be JSON-serialized with no additional code, leading to the additional advantage of being able to directly return `jsonify(SomeObject)` for many of the endpoints, using the same representation on both sides of the API. The downside is that a `SomeObject` containing a `name` attribute and other metadata is much clunkier to pass around than a bare `string`, `enum`, `NamedTuple`, or similar.

All situations that could use a `list(SomeObject)` are replaced with `dict{SomeObject.name:SomeObject}` (except for an image history: `list(Record)`, because it has a natural ordering). On the back of the API, this is done to simulate a database table indexed by `name`; on the front it is to support fast retrieval of a `Keyword` from an arbitrarily large `Category` and because the user should have access to a `SomeObject.name` but not necessarily the other fields, because `SomeObject` is designed for the database layer.


### Output format
Shown are JSON objects returned by endpoints. They will appear with SomeObject replaced by its representation so that the user does not have to deal with database semantics; they are shown compressed here for ease of explanation.

#### Keyword class
```
{
      "date_added": "Tue, 03 Dec 2019 17:46:22 GMT",
      "deprecated": false,
      "name": "Batman",
      "user_added": "<default>"
}
```
#### Record class
```
{
    "date_changed": "Tue, 03 Dec 2019 19:05:42 GMT",
    "keyword": KeywordObject
    "user_changed": "<default>"
}
```
#### Category class
```
{
    "date_added": "Tue, 03 Dec 2019 19:10:37 GMT",
    "keywords": {
        KeywordObject.name : KeywordObject
    },
    "name": "Character",
    "user_added": "<default>"
}
```
#### Image class
```
{
    "date_added": "Tue, 03 Dec 2019 20:50:00 GMT",
    "history": {
        Category.name : [ Record ]
    },
    "id": "00000000aaaaaaaa",
    "user_added": "<default>"
}

```

### API endpoints
Currently there is no user authentication and minimal error handling; any invalid requests result in undefined behavior.

#### Image API
```
GET /images/
{ 
      id: {
            Category.name: KeywordObject
      }
}


GET /images/<string:id>
id: {
      Category.name: KeywordObject
}

GET /history/images/
[ ImageObject ]

GET /history/images/<string:id>
ImageObject

POST /images/<string:id> { "category":cat_name, "keyword":kw_name }
```
Updates the given image's `cat_name` keyword to `kw_name`. Generates a `Record`.
```

DELETE /images/<string:id> { "category":cat_name }
```
Sets the keyword for the given image and category to `None`.
```

PUT /images/<string:id> { cat_name:kw_name }
```
Creates a new image with unique ID `id` associated with the given keywords.

#### Keyword API
All requests besides `GET` should be restricted to the `restricted_users` usergroup (not yet implemented).
```
GET /keywords/
[ Category.name ]

GET /keywords/<string:cat_name>
[ Keyword.name ]

GET /history/keywords/<string:cat_name>
{ Keyword.name:Keyword }

GET '/history/keywords/<string:cat_name>/<string:kw_name>'
Keyword

PUT /keywords/<string:cat_name>
```
Creates an empty category with the given `cat_name`. Warning: expensive; iterates through all images. Should be very rare.
```

PUT /keywords/<string:cat_name>/<string:kw_name>
```
Creates a keyword `kw_name` in the category `cat_name`.

```

DELETE /keywords/<string:cat_name>
```
Warning: expensive (iterates over images); irreversible (hard-deletes associated histories). Should be very rare.
```

DELETE /keywords/<string:cat_name>/<string:kw_name>
```
Soft-deletes the given keyword. Cheap and reversible.

### TODO
*  User authentication
*  Error handling
*  Get a real test suite, maybe use pytest
*  Docstrings
*  Linting
*  Build system

### Bonus features
*  Get/modify group of images by keyword contained, date range, or user touched
*  Real database
*  Autogenerated docs/API reference
