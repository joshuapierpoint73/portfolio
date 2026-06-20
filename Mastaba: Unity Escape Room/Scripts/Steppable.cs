using UnityEngine;

[RequireComponent(typeof(Animator))]
public class Steppable : MonoBehaviour
{
    public Animator animator;
    private bool playerInRange;

    private void Start()
    {
        animator = GetComponent<Animator>();  // Ensure Animator is correctly referenced
    }

    private void Update()
    {
        // Trigger animation if player is within range
        if (playerInRange)
        {
            animator.SetTrigger("TileSteppedOn");
        }
    }

    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Player"))
        {
            playerInRange = true;
        }
    }

    private void OnTriggerExit(Collider other)
    {
        if (other.CompareTag("Player"))
        {
            playerInRange = false;
        }
    }
}
