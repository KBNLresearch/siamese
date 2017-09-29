# Siamese
Siamese is a search interface for newspaper advertisements based on image similarity. It returns a set of nearest neighbors for a query image grouped by time period, which can be set at various lengths. It includes a graphical interface that presents the top 10 nearest neighbors along with a timeline of nearest neighbors for each year in the dataset.

## Background
Siamese was created during the KB Researcher-in-Residenceship of Melvin Wevers (UU) to explore a set of 426,777 high resolution images of historical newspaper advertisements from two Dutch national newspapers: Algemeen Handelsblad (1945-1969) and NRC Handelsblad (1970-1994). Vector representations of the original images were obtained from the next-to-last layer of the [Tensorflow Inception image classifier] (https://github.com/tensorflow/models/blob/master/tutorials/image/imagenet/classify_image.py) containing a 2048 float description of the image. A set of thumnails scaling down the images to a maximum height of 300 pixels was generated to speed up access over the web. 

## Usage
The image vector representations were indexed for approximate nearest neighbor search with [Annoy] (https://github.com/spotify/annoy), with the option of creating indices for a number of different time scales. Given the [availability of appropriately structured data] (http://lab.kb.nl/dataset/siameset), indices for e.g. each year and decade can be built with:

```python
import annoy_indexer

indexer = annoy_indexer.AnnoyIndexer(vector_dir='vectors', index_dir='indices-eucl', n_dimensions=2048, metric='euclidean')
indexer.build(n_trees=100, step_sizes=[10, 1])
```   

These can now be queried with an identifier for a specific image from the set. To retrieve, for example, the 5 nearest neighbors for each decade:

```pyhton
indexer.load(step_sizes=[10])
indexer.query_all('KBNRC01:000028496:mpeg21:a0065', n_nns=[5])
```

## Web API
Running `annoy_web.py` starts a Bottle web application that accepts parameters:

- `urn` the identifier of the query image
- `nns` the number of nearest neighbors to be returned
- `step` the time scale for the query specified as number of years
- `vectors` whether or not the vectors of the images should be included in the response

## Online demo
- An online demo of the Siamese graphical interface is available at http://kbresearch.nl/siamese/
- The web API can be accessed at http://kbresearch.nl/annoy/query

## More information
For more information, instructions and examples, see http://lab.kb.nl/tool/siamese.
