using UnityEngine;

public class PlayerMovement : MonoBehaviour
{
    public CharacterController controller;

    public float speed = 12f;
    public float gravity = -9.81f * 3; // Adjusted gravity for better response
    public float jumpHeight = 3f;

    public Transform groundCheck;
    public float groundDistance = 0.5f; // Radius for ground detection
    public LayerMask groundMask;

    private Vector3 velocity;
    private bool isGrounded;

    void Update()
    {
        // Check if the player is grounded after moving
        isGrounded = Physics.CheckSphere(groundCheck.position, groundDistance, groundMask);

        // Reset downward velocity if grounded
        if (isGrounded && velocity.y < 0)
        {
            velocity.y = -2f; // Small negative value to keep grounded
        }

        // Get player movement input
        float x = Input.GetAxis("Horizontal");
        float z = Input.GetAxis("Vertical");
        Vector3 move = transform.right * x + transform.forward * z;

        // Move player
        controller.Move(move * speed * Time.deltaTime);

        // Jump logic (only works when grounded)
        if (isGrounded && Input.GetButtonDown("Jump"))
        {
            velocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity); // Apply jump force
        }

        // Apply gravity after movement to ensure consistent behaviour
        velocity.y += gravity * Time.deltaTime;
        controller.Move(velocity * Time.deltaTime);
    }
}
