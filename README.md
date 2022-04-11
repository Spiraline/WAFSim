# WASim
FTL Simulator only for WA (Write Amplification)

## Requirement
- Python 3.x
- matplotlib
- tqdm

## Usage
**[Simulate with one configuration]**
```
python wafsim.py -c $(config file)
```

**[Parse MSRC trace into WASim trace]**

1. Download MSRC trace in [SNIA site](http://iotta.snia.org/traces/block-io)

2. Extract csv files in MSRC directory.

3. Execute `msrc_parser.py`. `*.trace` files will be created in same directory.

    ```
    python util/msrc_parser.py -i MSRC
    ```

**[Visualize MSRC trace result]**

```
python util/result_viz.py --dir $(result directory)
```

**[Visualize MSRC trace distribution]**

```
python util/trace_dist_viz.py --input $(.trace file or directory)
```

## Configurable Parameter

**[Simulation Parameters]**

| Parameter | Type | Description |
|:--:|:--:|:--:|
|`simulation_type`|str<br/>(`Synthetic`, `Trace`)|Determine simulation type|
|`simulation_tag`|str|Simulation identifier. Need for debug file name|
|`debug_victim_hist`|bool|Determine whether to log histogram<br/>of victim block's utilization distribution|
|`debug_final_u`|bool|Determine whether to log final utilization distribution|
|`debug_gc_stat`|bool|Determine whether to log GC statistics|
|`seed`|None, int|Set seed for random generator|
|`warmup_type`|None, 0, 1, 2|Determine warm-up type|
|`fill_percentage`|int|Fill percentage during warm-up|
|`invalid_percentage`|int|Invalid percentage during warm-up|

**[Synthetic Workload Parameters]**

These parameters are only valid when `simulation_type` is `Synthetic`.

| Parameter | Type | Description |
|:--:|:--:|:--:|
|`simulation_time`|int|Set simulation time|
|`iteration_num`|int|Set the number of simulation with same configuration|
|`working_set_percentage`|int|Percentage of LBA used|
|`workload_type`|0, 1, 2, 3|Determine workload type (e.g., seq write, hotcold)|
|`read_ratio`|float|Read request ratio|
|`locality`|float|Hot data ratio|

**[Trace Workload Parameters]**

These parameters are only valid when `simulation_type` is `Trace`.

| Parameter | Type | Description |
|:--:|:--:|:--:|
|`trace_path`|str<br/>(file, dir)|Path includes `.trace` file|
|`dynamic_capacity`|bool|If true, block number is adjusted<br/>to the largest address in trace file|
|`execute_percentage`|int|Percentage of request in trace to run|

**[SSD Parameters]**

| Parameter | Type | Description |
|:--:|:--:|:--:|
|`block_num`|int|-|
|`page_per_block`|int|-|
|`page_size`|int|-|
|`victim_selection_policy`|Greedy, CB, CAT, LCCB|-|
|`utilization_factor`|int|Only valid when victim selection policy is `LCCB`|
|`hotness_factor`|int|Only valid when victim selection policy is `LCCB`|
|`decay_factor`|int|Only valid when victim selection policy is `LCCB`|
|`gc_start_threshold`|float||
|`gc_mode`|0, 1|Determines whether GC reclaim a specific number<br/>or until a specific threshold|
|`gc_reclaim_block`|int|Only valid when `gc_mode` is 0|
|`gc_reclaim_threshold`|float|Only valid when `gc_mode` is 1|

## MSRC Example

1. Simulate GC with three policies (Change `victim_selection_policy` parameter)
    ```
    python wafsim.py -c config/msrc.cfg
    ```

2. Visualize result. `res.png` and `res.eps` will be created in workspace.
    ```
    python util/result_viz.py --dir res
    ```

![msrc_result](https://user-images.githubusercontent.com/44594966/161195763-72cd9f24-d20e-4a05-b525-6855684aea52.png)

