# XycLOps Vision

## Table of Contents
- [XycLOps Vision](#xyclops-vision)
  - [Document Purpose](#document-purpose)
  - [List](#list)
    - [Extraneous File I/O Reduction](#extraneous-file-io-reduction)
    - [Parallelism](#parallelism)
    - [Multi-platform Support](#multi-platform-support)
    - [Robust User Experience](#robust-user-experience)
    - [Non-Transient Analyses](#non-transient-analyses)
    - [Optimization Settings](#optimization-settings)
    - [Model Compatibility](#model-compatibility)
    - [Non-curvefit Optimization](#non-curvefit-optimization)


## Document Purpose
This document seeks to outline the developers’ thoughts on future improvements that could be made to XycLOps.  These observations are drawn from experience built during tool development and use.  Future contributors to the XycLOps tool are encouraged to draw inspiration from the following to make meaningful and impactful contributions.

## List
- ### Extraneous File I/O Reduction
   - Currently, every Xyce iteration outputs a file that is in turn parsed into memory for OptiXyce’s data operations.  This means every Xyce iteration has two associated file I/O operations.  Since I/O bound operations are notoriously slow, finding a way to eliminate this would most likely improve tool performance. (Maybe something like writing files to /dev/shm or memory mapped files)
- ### Parallelism
   - Currently, all Xyce iterations are run serially.  Finding a way to run Xyce iterations in a parallel fashion, perhaps even utilizing GPUsm would certainly increase tool performance. Note: This is hard and could require major optimization loop changes since there does not appear to be a trivial way to parallelize SciPy least_squares.
- ### Multi-platform Support
   - Currently, this tool is tailored to support a Windows experience.  While other platforms do work, keeping broad multi-platform support in mind throughout the future development process would improve the tool’s versatility and reach.
- ### Robust User Experience
   - Currently, Xyce offers few user experience features such as integrated explanations of key components and user input checks. Adding such features would make the tool more robust and resistant to unskilled usage.
- ### Non-Transient Analyses
   - Currently, the tool only supports transient analysis using Xyce.  Increasing the tool’s scope to support different analysis types that Xyce can use, especially AC analysis, would greatly increase the utility of this tool.
- ### Optimization Settings
   - Currently, the tool uses SciPy’s least_squares function for optimization workload with many key parameters hardcoded.  Making these parameters customizable by the user (with proper explanation) would make the tool much more responsive to the diverse use cases that entail different computational rigor for the optimization engine.
- ### Model Compatibility
   - Currently, OptiXyce can only work with certain circuit models.  Making the tool compatible with common circuit models and libraries (e.g. LTSpice default models) would greatly increase the tool’s reach and give users more freedom in their choice of schematic editor.
- ### Non-curvefit Optimization
   - Currently, OptiXyce only accepts specified voltage curve input as an optimization criteria.  Adding more types of optimization criteria could increase applicable use cases.

