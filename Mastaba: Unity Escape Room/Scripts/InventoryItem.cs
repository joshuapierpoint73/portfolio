using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using TMPro;

public class InventoryItem : MonoBehaviour, IPointerDownHandler
{
    public string thisName;

    private bool isEquippable;
    private GameObject itemPendingEquipping;
    public bool isNowEquipped;

    public bool isSelected;

    // Updates the drag-and-drop functionality based on whether the item is selected
    void Update()
    {
        var dragDrop = gameObject.GetComponent<DragDrop>();

        // Disable drag-and-drop functionality if the item is selected
        dragDrop.enabled = !isSelected;
    }

    // Handles the right-click interaction with the item
    public void OnPointerDown(PointerEventData eventData)
    {
        if (eventData.button == PointerEventData.InputButton.Right)
        {
            // Equip the item if it is equippable, not already equipped, and there is space in the quick slots
            if (isEquippable && !isNowEquipped && !EquipSystem.Instance.CheckIfFull())
            {
                EquipSystem.Instance.AddToQuickSlots(gameObject);
                isNowEquipped = true;
            }
        }
    }
}
