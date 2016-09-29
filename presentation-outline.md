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

### More examples

Numpy can make things more beautiful:

    a = list(range(10))
    b = list(range(10))
    c = [aa + bb for aa, bb in zip(a, b)]

    a = np.arange(10)
    b = np.arange(10)
    c = a + b

Or ugly:

```
x = [[1] * 3, [1] * 2]
y = [[0] * 2, [0] * 5]

z = [sum(zz, []) for zz in zip(x, y)]
z
# [[1, 1, 1, 0, 0], [1, 1, 0, 0, 0, 0, 0]]

x = np.array([np.ones(3), np.ones(2)])
y = np.array([np.zeros(2), np.zeros(5)])

z = np.empty(len(x), dtype=object)
for i in range(len(x)):
    z[i] = np.concatenate([x[i], y[i]])

z
# array([array([ 1.,  1.,  1.,  0.,  0.]),
#        array([ 1.,  1.,  0.,  0.,  0.,  0.,  0.])], dtype=object)
```

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
    * ~10x expansion of data size, turns "lots" of data into "too much"

HDF5
* Why it's appealing
  * Compact on-disk storage
  * Constant-time (O(1)) indexing into (some) data

* Why it didn't work
  * ETL
  * Jagged arrays in Numpy are clunky

### Design Plan

1. We keep accessing the raw data files and reading them into some other storage method convenient for analysis.
2. We keep changing that storage method
3. Create a layer between storage and analysis that exposes something consistent to allow future changes to storage layer without requiring re-write of analysis code. (Design pattern!)

### Result: Creation of Multiworm

The interface was designed to make common tasks easy and convenient.

* Get a single blob by ID
* Get all the blobs
* Get where the blob started/ended
* Get all blobs that existed at a specific time
* Get the closest image in time

### Additional Problem

Loading *all* the data is too much to handle, and usually not needed. Using lazy proxies (another design pattern) can help.
