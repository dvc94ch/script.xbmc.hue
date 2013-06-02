How to organize my lights in to groups
--------------------------------------

1. run "pip install phue" from the commandline.
2. open the idle python gui
3. type:    import phue
            b = phue.Bridge('substitute with the ip address of your bridge.')
4. press the button on your bridge
5. type:    b.connect()
            l = b.get_light_objects('list')
            for i in l:
                print i.light_id, i.name
                
6. create groups:
            b.create_group('group name', [comma separated list of the light ids you want to group])
7. check out your work:
            b.get_group()
8. congratulations, you're done

"Use all lights" doesn't work for me
------------------------------------

If the add-on is configured to "Use all lights", bulb number 2 has a 
special function. This bulb is "leading", ie the settings from this 
bulb are used for the whole group. Make sure this light is turned on 
when you start XBMC. If not, the add-on thinks the complete group is 
turned off.
