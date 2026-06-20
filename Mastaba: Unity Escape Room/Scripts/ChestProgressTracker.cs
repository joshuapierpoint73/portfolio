using System.Collections.Generic;
using UnityEngine;

public class ChestProgressTracker : MonoBehaviour
{
    public static ChestProgressTracker Instance;

    private HashSet<string> unlockedChests = new HashSet<string>();

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    public void UnlockChest(string chestName)
    {
        if (!unlockedChests.Contains(chestName))
        {
            unlockedChests.Add(chestName);
            Debug.Log($"Chest unlocked: {chestName}");
        }
    }

    public bool IsChestUnlocked(string chestName)
    {
        return unlockedChests.Contains(chestName);
    }

    public List<string> GetUnlockedChests()
    {
        return new List<string>(unlockedChests);
    }

    public int GetUnlockedChestCount()
    {
        return unlockedChests.Count;
    }
}
