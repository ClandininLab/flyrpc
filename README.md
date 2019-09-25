# Introduction

This is a simple library for managing interactions between server programs and client programs.  In the future it would be interesting to explore using gRPC or zeromq.

# Prerequisites

**flyrpc** only supports Python3, so in the commands below, **pip** should refer to a Python3 install.  You can either install Python3 directly or through a package manager like Conda.

# Installation

1. Open a terminal, and note the current directory, since the **pip** command below will clone some code from GitHub and place it in a subdirectory called **src**.  If you prefer to place the cloned code in a different directory, you can specify that by providing the **--src** flag to **pip**.
2. Install **flyrpc** with **pip**:
```shell
> git clone https://github.com/ClandininLab/flyrpc.git
> cd flyrpc
> pip install -e .
```

If you get a permissions error when running the **pip** command, you can try adding the **--user** flag.  This will cause **pip** to install packages in your user directory rather than to a system-wide location.
