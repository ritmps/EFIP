using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.Scripting.Python;

[CustomEditor(typeof(Python_manager))]
public class Python_manager_editor : Editor
{
    Python_manager targetManager;
    
    private void OnEnable()
    {
        targetManager = (Python_manager)target;
    }

    public override void OnInspectorGUI()
    {
        if(GUILayout.Button("Launch Python Script", GUILayout.Height(35)))
        {
            string path = Application.dataPath + "/Python/log_names.py";
            PythonRunner.RunFile(path);

        }
    }    
}
