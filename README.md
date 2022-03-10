# openSecuritisation

This repository aims to demonstrate a number of technical elements in support of open source securitisation frameworks. The motivation and approach is [described more fully here](https://www.openriskmanagement.com/open-source-securitisation/)

More specifically, we propose the following:

* Specifying a securitisation structure (tranching) using a yaml file
* Specifying cashflow operations using lambda functions serialized in a yaml file
* Documenting the cashflow logic using a python file

![Cashflow Screenshot](cashflows.png)


# Dependencies
* ruamel.yaml for parsing and emitting yaml documents that are part of the specification
* numpy for storage and processing of vectors / matrices holding numerical data
* pickle for storage of data / objects not part of the specification

# Further Resources

* [Open Risk Manual](https://www.openriskmanual.org/wiki/Category:Securitisation)