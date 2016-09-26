# Waldo, wrappers, and magic methods

## Waldo
### Raison D'être

...to clean up the data from the Multi-Worm Tracker. The MWT emits tens of thousands of individual tracked objects over an hour, despite there only being a few dozen worms for it to observe.

### Scope of Problem
An average experiment lasts for 50000 frames, and in each frame there are approximately 2 million "blob-frame" tracking entries.

> Blob: a computer-vision term denoting something different than the surroundings.

### Everything begins with the data

Every time we test a new method or generate a plot, we need to read the data.

### Writing beautiful code takes time and experience

* experience with the application
* refactoring something you'll maybe use once then discard is not the greatest use of your time
* what part of your code is used frequently? focus on that

### What is beautiful code

* thoughtfully designed
* pleasant to use
* Examples:
  * requests
* PEP-8 does not beautiful code make; *it is almost orthogonal*

### Fantastic code is the triple-crown
* beautiful (good external design)
* idiomatic (good internal design)
  * use of generators
* clean (well-formatted, easy to read)
  * pep-8

## Case Study

### The pillar of Waldo

Multiworm - An adapter to load data. Does one thing: load data.

### Graveyard of forgotten ideas

MongoDB
* Why it's appealing
  * Just connect to the database to access and store data in an arbitrary document-based NoSQL system
  * Fast random lookups if indexed

* Why it didn't work
  * Loading a single experiment (ETL) took hours
  * Change in schema required discarding all data
  * Impossible to store all the data efficiently

HDF5
* Why it's appealing
  * Compact on-disk storage
  * Constant-time (O(1)) indexing into data

* Why it didn't work
  * ETL every time
