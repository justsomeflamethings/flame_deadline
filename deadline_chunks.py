import flame
import os.path

def getMainMenuCustomUIActions():
  project = flame.project.current_project.name

  action1 = {}
  action1['name'] = '1 frame'

  action2 = {}
  action2['name'] = '5 Frames'

  action3 = {}
  action3['name'] = '10 Frames'

  action4 = {}
  action4['name'] = '20 Frames'

  action5 = {}
  action5['name'] = '30 Frames'

  group1 = {}
  group1['name'] = 'Deadline Frame Per Task'
  group1['separator'] = 'below'
  group1['actions'] = ({'name': '01 frame'}, {'name': '03 frames'}, {'name': '05 frames'}, {'name': '10 frames'}, {'name': '20 frames'}, {'name': '30 frames'})


  return (group1)

def customUIAction(info, userData):

  project = flame.project.current_project.name

  if " frame" in info['name']:


    dialog = flame.messages.show_in_dialog(
    title ="Deadline Frame Per Task",
    message = "Would you like to set to %s per task?" % info['name'],
    type = "question",
    buttons = ["Confirm"],
    cancel_button = "Cancel")

# store deadline chunks setting in a file on shared storage

    if dialog == "Confirm":
      user_id = os.getlogin()
      last_update_file = '/Volumes/MY_SAN/.flamestore/userdata/%s/%s.deadline.%s' % (user_id, project, info['name'].split()[0])
      try:
        os.mkdir(os.path.dirname(last_update_file))
      except:
        pass
      os.system('rm /Volumes/MY_SAN/.flamestore/userdata/%s/%s.deadline.*' % (user_id, project))
      os.system('touch %s' % last_update_file)



    if dialog == "Cancel":
      pass
