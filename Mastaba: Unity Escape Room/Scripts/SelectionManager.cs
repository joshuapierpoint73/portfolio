using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;


public class SelectionManager : MonoBehaviour
{
    public static SelectionManager Instance { get; private set; }

    public bool onTarget;
    public GameObject selectedObject;
    public GameObject interactionInfoUI;
    public Text interactionText;

    public Image centerDotImage;
    public Image handIcon;
    public bool handIsVisible;

    private ChestLockSystem currentChestLock;

    private void Awake()
    {
        // Ensure there is only one instance of SelectionManager
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
        }
        else
        {
            Instance = this;
        }
    }

    private void Start()
    {
        // Initialise the interaction text component
        onTarget = false;
        interactionText = interactionInfoUI.GetComponent<Text>();
    }

    private void Update()
    {
        // Raycast from the mouse position to detect interactable objects
        Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
        if (Physics.Raycast(ray, out RaycastHit hit))
        {
            var selectionTransform = hit.transform;
            InteractableObject interactable = selectionTransform.GetComponent<InteractableObject>();

            if (interactable && interactable.playerInRange)
            {
                // Display the interaction message when the object is interactable
                interactionText.text = interactable.GetInteractionMsg();
                interactionInfoUI.SetActive(true);
                selectedObject = interactable.gameObject;
                onTarget = true;

                // Show the hand icon for specific interactable object tags
                if (interactable.CompareTag("Pickable") || interactable.CompareTag("Container") ||
                    interactable.CompareTag("PharoahBust") || interactable.CompareTag("CatStatue") ||
                    interactable.CompareTag("Harp") || interactable.CompareTag("Sphinx")|| interactable.CompareTag("SetHint"))
                { 
                    centerDotImage.gameObject.SetActive(false);
                    handIcon.gameObject.SetActive(true);
                    handIsVisible = true;
                }
                else
                {
                    centerDotImage.gameObject.SetActive(true);
                    handIcon.gameObject.SetActive(false);
                    handIsVisible = false;
                }
            }
            else
            {
                // Hide interaction UI if no interactable object is in range
                ResetInteractionUI();
            }
        }
        else
        {
            // Reset UI if no object is being targeted
            ResetInteractionUI();
        }
    }

    private void ResetInteractionUI()
    {
        onTarget = false;
        interactionInfoUI.SetActive(false);
        centerDotImage.gameObject.SetActive(true);
        handIcon.gameObject.SetActive(false);
        handIsVisible = false;
    }

    public void DisableSelection()
    {
        // Disable all selection UI and interaction elements
        handIcon.enabled = false;
        centerDotImage.enabled = false;
        interactionInfoUI.SetActive(false);
        selectedObject = null;
    }

    public void EnableSelection()
    {
        // Enable all selection UI and interaction elements
        handIcon.enabled = true;
        centerDotImage.enabled = true;
        interactionInfoUI.SetActive(true);
    }
}
