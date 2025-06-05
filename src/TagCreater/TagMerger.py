from fuzzywuzzy import fuzz


# Tag에서 중복 제거
def MergeCleanTags(*tagLists, threshold=80):
    tags = []
    for tagList in tagLists:
        for item in tagList:
            if not any(
                fuzz.ratio(item.lower(), existing.lower()) >= threshold
                for existing in tags
            ):
                tags.append(item)

    # 줄임말 제거
    finalTags = tags[:]
    for item in tags:
        for other in tags:
            if item != other and other in item and other in finalTags:
                finalTags.remove(other)
    return finalTags
