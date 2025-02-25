### Ongoing testing of urlcannonisation ethod for implication into url-based data identification ###

1 - url parse assembly needs to be formatted for known domain variations (youtube.com/youtu.be) for example

2 - expand_redirect => be implemented first? may save resources by reducing obsolete proccesses
=> may be essential for content registration?

3 - Comparing end points after each modification of the url => keep continueing untill a different endpoint is reached and then reverting to the previous url that worked

4 - 'known_tracking_params' only affected agfter "?", e.g. "si" is triggered by "?si...", but not asib123 for example