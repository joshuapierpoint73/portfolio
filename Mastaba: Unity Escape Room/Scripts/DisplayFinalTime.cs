using UnityEngine;
using TMPro;  // Use TMPro namespace for TextMeshProUGUI

public class DisplayFinalTime : MonoBehaviour
{
    public TextMeshProUGUI finalTimeText;  // UI TextMeshProUGUI element to display the final time

    void Start()
    {
        // Retrieve the final time from PlayerPrefs
        float finalTime = PlayerPrefs.GetFloat("FinalTime", 0);

        // Convert time to minutes and seconds
        int minutes = Mathf.FloorToInt(finalTime / 60);
        int seconds = Mathf.FloorToInt(finalTime % 60);

        // Display the final time in the UI using TextMeshPro
        finalTimeText.text = string.Format("Time Remaining: {0:00}:{1:00}", minutes, seconds);
    }
}
