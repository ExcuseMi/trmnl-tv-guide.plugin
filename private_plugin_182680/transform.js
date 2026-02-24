function transform(input) {
  const apiToken = input.trmnl.plugin_settings.custom_fields_values.api_token;
  const channels = input.trmnl.plugin_settings.custom_fields_values.channel_data || 
                   input.trmnl.plugin_settings.custom_fields_values.channels || [];
  
  let now, offset;
  
  // Handle stub mode vs real data
  if (apiToken === "stub") {
    const firstChannelResponse = input.IDX_0;
    if (firstChannelResponse && firstChannelResponse.data && firstChannelResponse.data[0]) {
      const firstItemDate = new Date(firstChannelResponse.data[0].start);
      const year = firstItemDate.getFullYear();
      const month = String(firstItemDate.getMonth() + 1).padStart(2, '0');
      const day = String(firstItemDate.getDate()).padStart(2, '0');
      const targetTime = `${year}-${month}-${day} 22:00:00`;
      now = new Date(targetTime).getTime();
    } else {
      now = Date.now();
    }
    offset = 28800;
  } else {
    now = Date.now();
    offset = input.trmnl?.user?.utc_offset || 0;
  }
  
  const processedChannels = [];
  
  channels.forEach((channel, idx) => {
    const channelParts = channel.split('|');
    const channelId = channelParts[0] || "";
    const channelName = channelParts[1] || "";
    
    const channelKey = `IDX_${idx}`;
    const channelResponse = input[channelKey];
    
    if (!channelResponse || channelResponse.status === "error") {
      processedChannels.push({
        name: channelName,
        error: channelResponse?.message || "No data available",
        items: []
      });
      return;
    }
    
    const channelItems = channelResponse.data || [];
    
    if (!Array.isArray(channelItems) || channelItems.length === 0) {
      processedChannels.push({
        name: channelName,
        items: []
      });
      return;
    }
    
    const sortedItems = channelItems
      .filter(item => item && item.start && item.stop)
      .sort((a, b) => {
        const aStart = new Date(a.start).getTime();
        const bStart = new Date(b.start).getTime();
        return aStart - bStart;
      });
    
    const processedItems = [];
    let nextIsEmphasis2 = false;
    
    for (const item of sortedItems) {
      const itemStart = new Date(item.start).getTime();
      const itemStop = new Date(item.stop).getTime();
      
      // Skip past items
      if (itemStop <= now) continue;
      
      let emphasis = 1;
      let shadeGray = "text--gray-40";
      
      if (itemStart <= now && now < itemStop) {
        emphasis = 3;
        shadeGray = "";
        nextIsEmphasis2 = true;
      } else if (nextIsEmphasis2) {
        emphasis = 2;
        shadeGray = "text--gray-20";
        nextIsEmphasis2 = false;
      }
      
      const adjustedTimeMs = itemStart + (offset * 1000);
      const adjustedDate = new Date(adjustedTimeMs);
      
      processedItems.push({
        title: item.title || "",
        sub_title: item.sub_title || item.subTitle || "",
        description: item.description || item.desc || "",
        adjusted_time: adjustedDate.toISOString(),
        emphasis: emphasis,
        shade_gray: shadeGray
      });
      
      if (processedItems.length >= 10) break;
    }
    
    processedChannels.push({
      name: channelName,
      items: processedItems
    });
  });
  
  return {
    channels: processedChannels
  };
}