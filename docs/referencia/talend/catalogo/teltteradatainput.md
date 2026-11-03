# teltteradatainput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltteradatainput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltteradatainput -->

# Mapping data using a subquery

The sample Job described in this scenario maps the data from two input tables, PreferredSubject and CourseScore, to the output table, TotalScoreOfPreferredSubject, using a subquery.

## Prerequisite

Ensure that you have added an Oracle database connection in the Metadata &gt; Db Connections section prior to creating the Job. For more information, see [Centralizing database connections](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/centralizing-database-metadata).

## The Standard Job and the Prejob design

In this scenario, design the Standard Job such as the following:

![](https://help.qlik.com/talend/en-US/components/Resources/images/teltoracleMap_subquery_scenario.png)

Design the Prejob that includes the data in this scenario as follows: ![](https://help.qlik.com/talend/en-US/components/Resources/images/teltoracleMap_subquery_comp7.png)

The PreferredSubject table contains the student's preferred subject data. To reproduce this scenario, you can load the following data to the Oracle table from a CSV file:

```
SeqID;StuName;Subject;Detail
1;Amanda;art;Amanda prefers art.
2;Ford;science;Ford prefers science.
3;Kate;art;Kate prefers art.
```

The CourseScore table contains the student's subject score data. To reproduce this scenario, you can load the following data to the Oracle table from a CSV file:

```
SeqID;StuName;Subject;Course;Score;Detail
1;Amanda;science;math;85;science score
2;Amanda;science;physics;75;science score
3;Amanda;science;chemistry;80;science score
4;Amanda;art;chinese;85;art score
5;Amanda;art;history;95;art score
6;Amanda;art;geography;80;art score
7;Ford;science;math;95;science score
8;Ford;science;physics;85;science score
9;Ford;science;chemistry;80;science score
10;Ford;art;chinese;75;art score
11;Ford;art;history;80;art score
12;Ford;art;geography;85;art score
13;Kate;science;math;65;science score
14;Kate;science;physics;75;science score
15;Kate;science;chemistry;80;science score
16;Kate;art;chinese;85;art score
17;Kate;art;history;80;art score
18;Kate;art;geography;95;art score
```

Before the Job execution, the output table TotalScoreOfPreferredSubject does not contain any data:

```
SeqID;StuName;PreferredSubject;TotalScore
```

### In this section

* [Creating the Prejob](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltteradatainput-teltteradatamap-teltteradataoutput-creating-prejob-create?id=1770)
* [Adding the components](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltteradatainput-teltteradatamap-teltteradataoutput-adding-components-standard-component-add?id=1771)
* [Configuring the input components](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltteradatainput-teltteradatamap-teltteradataoutput-configuring-input-components-standard-component-select?id=1772)
* [Configuring the output component](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltteradatainput-teltteradatamap-teltteradataoutput-configuring-output-component-standard-component-select?id=1773)
* [Configuring data mapping to generate a subquery](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltteradatainput-teltteradatamap-teltteradataoutput-configuring-data-mapping-to-generate-subquery-standard-component-click?id=1774)
* [Mapping the input and output schemas](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltteradatainput-teltteradatamap-teltteradataoutput-mapping-input-and-output-schemas-standard-component?id=1775)
* [Executing the Job](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltteradatainput-teltteradatamap-teltteradataoutput-executing-job-standard-component-click?id=1776)

**Related information**

* [tELTTeradataInput](https://help.qlik.com/talend/en-US/components/8.0/elt-teradata/teltteradatainput)
* [tELTTeradataMap](https://help.qlik.com/talend/en-US/components/8.0/elt-teradata/teltteradatamap)
* [tELTTeradataOutput](https://help.qlik.com/talend/en-US/components/8.0/elt-teradata/teltteradataoutput)
