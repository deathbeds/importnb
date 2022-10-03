# `pytest` integration

since `importnb` transforms notebooks to python documents we can use these as source for tests.
`importnb`s `pytest` extension is not fancy, it only allows for conventional pytest test discovery. 

`nbval` is alternative testing tools that validates notebook outputs. this style is near to using notebooks as `doctest` while `importnb` primarily adds the ability to write `unittest`s in notebooks. adding tests to notebooks help preserve them over time.
