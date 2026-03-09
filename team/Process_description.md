# Description of the given data and its potential analysis

## Parameters
- Voltage(V) 
- Flank ratio(F_r)
- Delta t2(dt2)

## Part 1. {V, F_r} combination for a single chip  

**In a chip, for every combination of  V, F_r, all the dt2`s [-1100, -900, -700, -500, -300] (5 in total) are tested. 
On every sheet 6 ‘coverages’ (amount of ink) are printed 
For a single combination of V, F_r we print 6 coverages for 5 dt2 values => 5*6 = 30 sets of data per chip for a given {V, F_r}** 

## Part2. Calculation for every chip and every nozzle for a {V, F_r} combination

**For 1120 nozzles in every chip (30) we get in total = 1120*30*30(sets of data described earlier for single combination of V, F_r) = 1,008,000 SD values**

## Part3. Waveform sets for all possible {V, F_r} combinations 
- 30 different {V, F_r} combinations  
- 5 dt2 per {V, F_r} 
- 6 coverage levels per {V, F_r, dt2}  
30 * 30 = 900 
- 6 repeated sheets per waveform set
900 * 6 = 5400 - number of data sets for all combinations of available {V, F_r} and dt2 for 6 coverage levels 
repeated 6 times 

## Part4. Total sum  
- 4 colors
- 30 chips per color
- 1120 nozzles per chip
 
**Total of: 5400 * 4 ∗ 30 ∗ 1120  = 725,760,000 individual samples**



