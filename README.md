# UCLA CS 131 Fall 2023: Project Repo

This repo contains an adapted autograder and fully functional solution for UCLA's CS 131: Programming Languages class. Project specification details are available on the CS 131 [class website](https://ucla-cs-131.github.io/fall-23-website/), and a brief summary is included below (adapted directly from the project specifications written by Carey Nachenberg and his TAs).

## Project 1: Basic Interpreter
This project builds upon the Project 1 provided skeleton framework, but is otherwise original and implements the following features:

* `int` and `string` types
* Storing and reading of variables
* Error throwing, printing, and reading in user input
* Integral addition and subtraction

An implementation of this project can be found in the `./Brewin/interpreterv1.py` file.

## Project 2: Brewin
This project builds upon Project 1 and adds the below core features (among other smaller changes):

* Introduction of the `bool` type
* Common arithmetic and logical operations
* Function definitions and function calls (beyond just `main()`)
* Common control flow constructs (`for` and `while` loops)

An implementation of this project can be found in the `./Brewin/interpreterv2.py` file.

## Project 3: Brewin++
This project builds upon Project 2 and adds the below core features (among other smaller changes):

* Brewin++ now supports first-class functions (e.g., passing functions as arguments, returning functions, storing functions in variables)
* Brewin++ now supports lambdas/closures
* Brewin++ now supports pass-by-reference parameter passing in addition to pass-by-value
* Brewin++ now supports limited type coercions  

An implementation of this project can be found in the `./Brewin/interpreterv3.py` file.

## Project 4: Brewin#
This project builds upon Project 3 and adds the below core features (among other smaller changes):

* Brewin# now has support for objects much like those used in JavaScript (Brewin# does NOT have classes, just objects). Objects may have member fields and methods 
* Brewin# now supports prototypal inheritance, so an object can inherit methods/fields from a prototype object (and this can chain across multiple such prototype objects)
* Brewin# programs must also support all operations on objects (e.g., passing them as parameters, returning them, capturing them in closures, comparing them for equality, etc.)

An implementation of this project can be found in the `./Brewin/interpreterv4.py` file.