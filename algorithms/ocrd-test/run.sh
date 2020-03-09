#!/bin/bash
INPUTFILE=/data/input/test_data
TMPDIR=$(mktemp -d)
TMPDIR=/data/tmp
mkdir $TMPDIR

cd $TMPDIR
ocrd workspace init ws
cd ws
mkdir OCR-D-IMG
tar -C $TMPDIR/ws/OCR-D-IMG -x -v -f $INPUTFILE
for i in $TMPDIR/ws/OCR-D-IMG/*.tif; do
  base=`basename ${i} .tif`
  ocrd workspace add -G OCR-D-IMG -i ${base} -g P_${base} -m image/tif ${i}
done

ocrd process \
  "olena-binarize -I OCR-D-IMG -O OCR-D-BIN -p '{\"impl\": \"sauvola-ms-split\"}'" \
  "cis-ocropy-denoise -I OCR-D-BIN -O OCR-D-BIN-DENOISE -p '{\"level-of-operation\":\"page\"}'" \
  "anybaseocr-deskew -I OCR-D-BIN-DENOISE -O OCR-D-BIN-DENOISE-DESKEW" \
  "anybaseocr-crop -I OCR-D-BIN-DENOISE-DESKEW -O OCR-D-CROP" \
  "cis-ocropy-segment -I OCR-D-CROP -O OCR-D-SEG-REG -p '{\"level-of-operation\":\"page\"}'" \
  "cis-ocropy-deskew -I OCR-D-SEG-REG -O OCR-D-SEG-REG-DESKEW -p '{\"level-of-operation\":\"region\"}'" \
  "cis-ocropy-clip -I OCR-D-SEG-REG-DESKEW -O OCR-D-SEG-REG-DESKEW-CLIP -p '{\"level-of-operation\":\"region\"}'" \
  "cis-ocropy-segment -I OCR-D-SEG-REG-DESKEW-CLIP -O OCR-D-SEG-LINE -p '{\"level-of-operation\":\"region\"}'" \
  "cis-ocropy-resegment -I OCR-D-SEG-LINE -O OCR-D-SEG-LINE-RESEG" \
  "cis-ocropy-dewarp -I OCR-D-SEG-LINE-RESEG -O OCR-D-SEG-LINE-RESEG-DEWARP" \
  "calamari-recognize -I OCR-D-SEG-LINE-RESEG-DEWARP -O OCR-D-OCR -p '{\"checkpoint\":\"/models/calamari_models-1.0/fraktur_historical/*.ckpt.json\"}'"

#cd $TMPDIR/ws/
#tar -cf /data/output * --no-same-owner
