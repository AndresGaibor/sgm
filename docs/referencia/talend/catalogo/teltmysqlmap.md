# teltmysqlmap

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltmysqlmap  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltmysqlmap -->

# Mapping date using an Alias table

This scenario describes a Job that maps information from two input tables and an alias table, serving as a virtual input table, to an output table. The *employees* table contains employees' IDs, their department numbers, their names, and the IDs of their respective managers. The managers are also considered as employees and hence included in the *employees* table. The *dept* table contains the department information. The alias table retrieves the names of the managers from the *employees* table.

![](https://help.qlik.com/talend/en-US/components/Resources/images/Use_Case_tELTMysqlMap2-1.png)

### In this section

* [Building a Job](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltmysqlmap-teltmysqlinput-teltmysqloutput-building-job-drop?id=1778)
* [Connecting the components](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltmysqlmap-teltmysqlinput-teltmysqloutput-connecting-components-connect?id=1779)
* [Configuring the Job](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltmysqlmap-teltmysqlinput-teltmysqloutput-configuring-job-click?id=1780)
* [Running the Job](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltmysqlmap-teltmysqlinput-teltmysqloutput-running-job-save?id=1781)

**Related information**

* [tELTMysqlInput](https://help.qlik.com/talend/en-US/components/8.0/elt-mysql/teltmysqlinput)
* [tELTMysqlMap](https://help.qlik.com/talend/en-US/components/8.0/elt-mysql/teltmysqlmap)
* [tELTMysqlOutput](https://help.qlik.com/talend/en-US/components/8.0/elt-mysql/teltmysqloutput)
