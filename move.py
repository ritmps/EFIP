import UnityEngine as ue

objects = ue.Object.FindObjectsOfType(ue.GameObject)
for parents in objects:
    if parents.name == 'puck2':
        ue.Debug.Log(parents.name)
        parents.transform.position += parents.transform.position.up * 10
        ue.Debug.Log(str(parents.transform.position))
