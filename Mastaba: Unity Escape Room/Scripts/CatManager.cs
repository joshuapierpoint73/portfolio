using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CatManager : MonoBehaviour
{
    public static CatManager Instance; // Singleton instance of CatManager
    private Dictionary<GameObject, float> statueTargets = new Dictionary<GameObject, float>(); // Stores statues and their target rotations
    public GameObject[] statues; // Array of all cat statues
    public GameObject door; // Door to open when statues are correctly positioned

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject); // Ensure only one instance exists
        }
    }

    private void Start()
    {
        for (int i = 0; i < statues.Length; i++)
        {
            statueTargets.Add(statues[i], AssignTargetRotation(i)); // Assign target rotations to each statue
        }
    }

    // Assigns the correct target rotation for each statue
    private float AssignTargetRotation(int index)
    {
        float[] predefinedRotations = { 0f, 180f, 270f }; // Predefined correct rotations
        return index < predefinedRotations.Length ? predefinedRotations[index] : 0f;
    }

    // Rotates the selected statue by 90 degrees and checks if all are correctly positioned
    public void RotateStatue(GameObject statue)
    {
        statue.transform.Rotate(Vector3.up, 90f, Space.Self);
        CheckAllStatues();
    }

    // Checks if all statues are in their correct positions
    private void CheckAllStatues()
    {
        foreach (var entry in statueTargets)
        {
            float normalisedRotation = entry.Key.transform.eulerAngles.y % 360f;
            if (!Mathf.Approximately(normalisedRotation, entry.Value))
            {
                return; // If any statue is incorrect, stop checking
            }
        }
        TriggerAllStatuesCorrectEvent(); // If all are correct, trigger event
    }

    // Opens the door when all statues are correctly positioned
    private void TriggerAllStatuesCorrectEvent()
    {
        door.GetComponent<DoorScript>().Open();
    }
}

