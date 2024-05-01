import yaml
import json
import pprint

yaml_input_file = file('input.yml', 'r');
json_input_file = file('input.json', 'r');
json_str = json_input_file.read();
return_value = True;
debug_flag =1 ;

# Convert both yaml and json files into dict 
yaml_dict = yaml.load(yaml_input_file)
json_dict = json.loads(json_str)

# Convert dict.keys() into a set, and compare them
left = yaml_dict
right = json_dict['manifest']
# Note: Saving dict into set set(dict) will only store the keys.
# Alternatively, use set(dict.itmes()), which stores tuple(key, value), for levaging default set functions
diff = dict()
diff['different'] = {k for k in set(left) & set(right) if left[k]!=right[k]}

if len(set(left) ^ set(right)):
  print 'Symmetric difference is Found in yaml & json dictionaries.' 
  return_value = False;
if len(diff['different']):
  print 'Found items in dictionraries with same key but different values' 
  return_value = False;

if debug_flag and return_value == False:
  print "--- yaml_dict ---"
  #print yaml.dump(yaml_dict, default_flow_style=False)
  pprint.pprint (yaml_dict)
  print "--- json_dict ---"
  pprint.pprint (json_dict[u'manifest'])
  #print json.dumps(json_dict, indent=1)
  left = set ('abcd')
  right = set ('cdef')
  print "Keys found in yaml file only = ", (set(left) - set(right));
  print "Keys found in json file only = ", (set(right) - set(left));
  print "Items with same key but diff values = ",  diff['different'];

exit (return_value);
