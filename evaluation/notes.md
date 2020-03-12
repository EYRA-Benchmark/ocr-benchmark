ocrevalUAtion (https://github.com/impactcentre/ocrevalUAtion)

See wiki page for unicode character equivalences:
Convert table using LETTER\s(%c+) or LIGATURE\s(%t+)

docker container available. See ochre repository (https://github.com/KBNLresearch/ochre) with cwl workflows for running and extraction.

test:
```bash
java -cp /ocrevalUAtion/target/ocrevaluation.jar eu.digitisation.Main -gt testData/6271086/GT/X0000004.txt -ocr testData/6271086/txt/X0000004.txt -o output/test_out.html
```

test_out.html start:
```html
<h2>General results</h2>
<table border="1">
<tr>
<td>CER</td><td>n/a</td>
</tr>
<tr>
<td>WER</td><td>n/a</td>
</tr>
<tr>
<td>WER (order independent)</td><td>n/a</td>
</tr>
</table>
<h2>Difference spotting</h2>
<table border="1">
</table>
<h2>Error rate per character and type</h2>
<table border="1">
<tr>
<td>Character</td><td>Hex code</td><td>Total</td><td>Spurious</td><td>Confused</td><td>Lost</td><td>Error rate</td>
</tr>
<tr>
<td>n/a</td><td>n/a</td><td>n/a</td><td>n/a</td><td>n/a</td><td>n/a</td><td>n/a</td>
</tr>
</table>
```


ToDo:
- Calculate score for overall bounding box match
    - Add Jaccard Indices and normalize
- Extract text from TextRegion and pass to ocrevalUAtion
- Combine ocrevalUAtion scores into single score

Later:
- Bag of Words approach
  - Per document?
  - Per TextRegion

