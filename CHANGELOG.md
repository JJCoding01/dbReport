# Change Log

## v0.3.3a2
 - Corrected bug where views listed in the `ignore_views` key from layout file 
   were still getting rendered 

## v0.3.3a1
 - Added tests and added CI on Travis
 - Added `Report.write` to write rendered output to files
 
 **Backwards Incompatible Changes**
 - Updated `Report.render` method to return dictionary of rendered reports 
 rather than write output directly to output files
 - Changed default parameter `parse` for `Report.render` to `False` (was `True`) 
