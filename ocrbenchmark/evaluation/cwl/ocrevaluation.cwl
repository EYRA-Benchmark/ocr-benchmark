#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["java", "-cp", "/Users/bweel/Software/projects/eyrabenchmark/ocrbenchmark/ocrbenchmark/evaluation/cwl/ocrevalUAtion-1.3.4.jar"]

requirements:
  - class: InitialWorkDirRequirement
    listing:
      - entryname: $(inputs.gt.nameroot)_out.html
        writable: true
        entry: |
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

arguments:
  - prefix: "-o"
    valueFrom: $(runtime.outdir)/$(inputs.gt.nameroot)_out.html
    position: 4
  - valueFrom: eu.digitisation.Main
    position: 1

successCodes: [1]

inputs:
  gt:
    type: File
    inputBinding:
      prefix: -gt
      position: 2
  ocr:
    type: File
    inputBinding:
      prefix: -ocr
      position: 3
  encoding:
    type: string?
    inputBinding:
      prefix: -e
      position: 5
  ignore_case:
    type: boolean?
    inputBinding:
      prefix: -ic
      position: 6
  ignore_diacritics:
    type: boolean?
    inputBinding:
      prefix: -id
      position: 7
  ignore_punctuation:
    type: boolean?
    inputBinding:
      prefix: -ip
      position: 8
  xmx:
    type: string?
    default: 5G
    inputBinding:
      prefix: -Xmx
      separate: false
      position: 0


outputs:
  out_file:
    type: File
    outputBinding:
      glob: $(inputs.gt.nameroot)_out.html