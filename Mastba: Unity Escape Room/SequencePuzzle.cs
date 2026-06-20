using UnityEngine;

public class SequencePuzzle : MonoBehaviour
{
    public GameObject triggerPlates;
    public GameObject nonTriggerPlates;
    public GameObject door;
    public bool allDown = false;
    public int plateDownNo;

    private bool doorOpened = false;  // Flag to ensure door sound is played only once

    public static SequencePuzzle Instance { get; private set; }

    private void Awake()
    {
        // Ensure only one instance of SequencePuzzle exists
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);
        }
    }

    private void Update()
    {
        plateDownNo = 0;
        bool allSteppedOn = true;

        // Check if all trigger plates are stepped on
        foreach (Transform child in triggerPlates.transform)
        {
            bool isSteppedOn = child.GetComponent<PadScript>().steppedOn;
            if (!isSteppedOn)
            {
                allSteppedOn = false;
            }
            else
            {
                plateDownNo++;
            }
        }

        // Check if any non-trigger plates are stepped on
        foreach (Transform child in nonTriggerPlates.transform)
        {
            if (child.GetComponent<PadScript>().steppedOn)
            {
                plateDownNo++;
            }
        }

        // Open the door if all trigger plates are stepped on and the door hasn't been opened yet
        if (allSteppedOn && !doorOpened)
        {
            door.GetComponent<DoorScript>().Open();
            doorOpened = true;  // Set the flag to true to prevent the door from opening again
        }

        // Reset all plates if more than 4 plates are down
        if (plateDownNo > 4)
        {
            ResetAllPlates();
        }
    }

    // Reset all plates
    private void ResetAllPlates()
    {
        foreach (Transform child in triggerPlates.transform)
        {
            child.GetComponent<PadScript>().ResetPlate();
        }

        foreach (Transform child in nonTriggerPlates.transform)
        {
            child.GetComponent<PadScript>().ResetPlate();
        }

        doorOpened = false;  // Reset the flag so the door can open again when the condition is met
    }
}
