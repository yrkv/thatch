
# Thatch


Extremely minimal experiment tracker.

Loosely inspired by systems such as Wandb and Aim, but trying to keep things simple and flexible.


### Overall Structure

- ***Run*** -- Structure used to store/track all data related to a particular experiment, including both tracked values and metadata which applies to the entire run.
- ***Root*** -- Location used by a run to store/write its data.
	- `MemoryRoot`: Keep everything entirely in memory of current process; pretty much equivalent to using ad-hoc list(s) of entries.
	- `DirectoryRoot`: Write run data to files within a directory.


