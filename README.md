# Take-Home Technical Test for Architect Role


## Overview

This take-home test is designed to evaluate your skills in both high-level design and practical implementation of an API to manage virtual machines (VMs).


## Part 1: High-Level Design

Design a platform that will allow end-users to create virtual machines and leverage GPUs.
Create a high-level design, including a diagram.


## Part 2: Technical Implementation

You will implement an API for managing VMs based on the design from Part 1.
This involves creating endpoints to provision and delete VMs, with all operations saved to a local database including created/updated timestamps.


### Requirements

- Python 3.10+


### Task

- **Define the Database Model**: Define the database model for storing VM information.
- **Implement the API Endpoints**: Define the endpoints for creating and deleting VMs.
- **Save VM States**: Save the state of the VMs in the local database.


### Additional Info

An SDK is provided to simulate the provisioning and deletion of VMs on the hypervisor layer; `from sdk import Client`.
It includes methods for authentication, creating VMs, and deleting VMs.
The SDK client's API key is set at the environment level and is not required in requests.


### Submission

Please provide a link to a public repository (e.g., GitHub) with your implementation.

We value your time and are more interested in your skills and approach rather than a "perfect" submission.
We don't expect more than a few hours' effort, so feel free to submit a partial submission.

Good luck!


### Getting Started

1. Install [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
2. Install dependencies with `poetry install`


### Running Tests

```bash
poetry run pytest
```