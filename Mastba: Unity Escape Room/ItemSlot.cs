using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

public class ItemSlot : MonoBehaviour, IDropHandler
{
    // Returns the item in the slot if it exists, otherwise returns null
    public GameObject Item
    {
        get
        {
            if (transform.childCount > 0)
            {
                return transform.GetChild(0).gameObject;
            }

            return null;
        }
    }

    // Handles the drop event when an item is dropped into the slot
    public void OnDrop(PointerEventData eventData)
    {
        Debug.Log("OnDrop");

        // If the slot is empty, set the dragged item to this slot
        if (!Item)
        {
            var draggedItem = DragDrop.itemBeingDragged;

            // Set the dragged item as a child of this slot and reset its position
            draggedItem.transform.SetParent(transform);
            draggedItem.transform.localPosition = Vector2.zero;

            // Check if the slot is a quick slot and update the item’s equip status
            var inventoryItem = draggedItem.GetComponent<InventoryItem>();

            if (transform.CompareTag("QuickSlot"))
            {
                inventoryItem.isNowEquipped = true;
            }
            else
            {
                inventoryItem.isNowEquipped = false;
            }

            // Recalculate the inventory list after the item is moved
            InventorySystem.Instance.ReCalculateList();
        }
    }
}
