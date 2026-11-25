# Demo results

Produced by `gold-checker demo <name> --show 10` on 25 November 2026, against the public files pinned by SHA-256 in `src/gold_checker/datasets.py`.

## Gold-answer check: FinQA test (1,147 items)

Format: finqa. Relative tolerance: 0.005.

| Result | Items |
|---|---|
| Checked | 1147 |
| Written answer agrees with gold value | 1017 |
| Percent-format slips (number right) | 28 |
| **Written answer disagrees with gold value** | **78** |
| Written answer empty or not a number | 24 |
| Program result differs from stored value | 4 |
| Program would not run | 0 |

Counting each page-question pair once: 101 of 1138 unique questions flagged (78 disagree, 23 empty or not a number).

Disagreements by kind: value 58, sign 11, scale_x1000 2, scale_/1000 4, scale_x1e6 1, yes/no 2.

### First 10 disagreements

| id | kind | written | gold value | question |
|---|---|---|---|---|
| ILMN/2008/page_82.pdf-1 | value | 7.47 | 1e-05 | during 2008 what was the share price of the warrants exercised\\n |
| CME/2010/page_91.pdf-1 | value | 29% | 0.27273 | what was the percentage change in receivables from brokers with in other current assets from 2009 to 2010? |
| MSI/2014/page_76.pdf-3 | value | 15.8% | 0.12159 | what was the percentage change in the weighted-average estimated fair value of employee stock options granted during from 2013 to 2014 |
| SNA/2007/page_49.pdf-4 | value | 2.7% | 2.02778 | what was the percentage change in the cash dividends paid per common share from 2006 to 2007 |
| RSG/2018/page_94.pdf-1 | sign | 11.9% | -0.11825 | as of december 31 , 2018 what was the percentage decline in the allowance for doubtful accounts |
| ECL/2016/page_52.pdf-1 | value | 43.7% | 0.00543 | what portion of cash and cash equivalents on hand are held in u.s . as of december 31 , 2016? |
| AMT/2012/page_118.pdf-2 | scale_x1e6 | 189625 | 0.18962 | pursuant to the agreement , on march 30 , 2012 , what was the approximate price for each site the company purchased in thousands |
| AMAT/2013/page_37.pdf-2 | scale_/1000 | 3829 | 38290.0 | what is the total return if 100000 are invested in s&p500 in 2008 and sold in 2011? |
| BLK/2014/page_120.pdf-2 | value | 29.63% | 349.0 | what percent of future notes are due by 2017? |
| SNA/2007/page_69.pdf-3 | value | -32.4% | -1.32432 | what was the percentage change in the minority interest from 2005 to 2006 |


## Gold-answer check: ConvFinQA dev (421 conversations)

Format: convfinqa. Relative tolerance: 0.005.

| Result | Items |
|---|---|
| Checked | 542 |
| Written answer agrees with gold value | 488 |
| Percent-format slips (number right) | 21 |
| **Written answer disagrees with gold value** | **24** |
| Written answer empty or not a number | 9 |
| Program result differs from stored value | 0 |
| Program would not run | 0 |

Counting each page-question pair once: 27 of 458 unique questions flagged (18 disagree, 9 empty or not a number).

Disagreements by kind: value 14, sign 9, scale_/1000 1.

### First 10 disagreements

| id | kind | written | gold value | question |
|---|---|---|---|---|
| Single_CDNS/2018/page_31.pdf-1:qa | scale_/1000 | 1877 | 18770.0 | what is the total return is $ 100000 are invested in s&p500 on january 1st , 2015 and sold at the end of 2016? |
| Double_STT/2008/page_83.pdf:qa_1 | value | 44% | 1.25 | what percent higher is the average var for foreign exchange products than that of interest rate products? |
| Single_CB/2010/page_88.pdf-1:qa | sign | 38.2% | -0.38206 | what was the percentage change of the net favorable prior period development from 2010 to 2008 |
| Single_IPG/2008/page_93.pdf-3:qa | value | 1.56% | 1.43416 | what is the total percentage decrease in future contingent acquisition obligations payable in cash from 2009-2013? |
| Single_PM/2015/page_85.pdf-1:qa | sign | 3.4% | -0.0339 | what is the percentage change in total debt from 2014 to 2015? |
| Single_TSCO/2017/page_31.pdf-2:qa | value | 73.4% | 0.7446 | compared to the s&p 500 ,what was the difference in percentage growth from the s&p 500 retail index . |
| Single_AMT/2012/page_125.pdf-1:qa | value | 1798334 | 180041.58004 | for the mtn group acquisition , what was the cost per tower ? . |
| Double_ABMD/2009/page_88.pdf:qa_0 | value | 5583331 | 16750002.0 | what are the total contingent payments relating to impella? |
| Double_AMT/2012/page_125.pdf:qa_0 | value | 1798334 | 180041.58004 | for the mtn group acquisition , what was the cost per tower ? . |
| Double_ETR/2011/page_341.pdf:qa_1 | value | 3.5% | 555.3 | what was the percentage change in net revenue in 2011 |


