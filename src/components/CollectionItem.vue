<template>
    <router-link :to="{ name: 'weapon', params: { weapon_id: weapon_id }}"><img class="coll" v-b-popover.hover="titleString" :title="tooltip_title" :src="image_url" /></router-link>
</template>

<script>
export default {
  name: 'CollectionItem',
  props: { 
    weapon_id: String,
    image_url: String,
    tooltip_title: String, 
    tooltip_content: Array
  },
  computed: {
    titleString: function() {
      return "Owned by: " + this.tooltip_content.join(', ');
    }
  }
}
</script>

<style lang="scss">
.coll {
  border-style: solid;
  border-width: 3px;
  border-color: #343a40;
}

</style>
