using UnityEngine;

public class PadScript : MonoBehaviour
{
    public Vector3 startPosition;
    public Vector3 endPosition;
    public float duration = 2.0f;  
    public bool playerInRange;  
    public bool steppedOn = false;  
    private float resetTimer = 8.0f;  
    private float elapsedTime = 0.0f;  

    void Start()
    {
        // Initialise start and end positions for the pad
        startPosition = transform.position;
        endPosition = new Vector3(startPosition.x, startPosition.y - 1, startPosition.z);
    }

    void Update()
    {
        // Check if the player is on the pad and move it
        if (playerInRange && elapsedTime < duration)
        {
            elapsedTime += Time.deltaTime;  
            transform.position = Vector3.Lerp(startPosition, endPosition, elapsedTime / duration); 
            steppedOn = true;  
        }

        // If the pad has been activated, start the reset timer
        if (steppedOn)
        {
            resetTimer -= Time.deltaTime;  
            if (resetTimer <= 0)
                ResetPlate();  
        }
    }

    // Resets the pad's position and the associated timers
    public void ResetPlate()
    {
        transform.position = startPosition;  
        elapsedTime = 0.0f;  
        steppedOn = false;  
        resetTimer = 8.0f;  
    }

    // Triggered when an object enters the pad's trigger zone
    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Player"))  
            playerInRange = true;  
    }

    // Triggered when an object exits the pad's trigger zone
    private void OnTriggerExit(Collider other)
    {
        if (other.CompareTag("Player"))  
            playerInRange = false; 
    }
}
