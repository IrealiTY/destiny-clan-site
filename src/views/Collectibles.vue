<template>
  <b-container fluid class="bg-dark">
    <h1>THE EXOTIC WEAPONS OUR GUARDIANS HAVE COLLECTED.</h1>
    <b-row>
      <div v-if="resources_collectibles_unowned[0].length > 0">
        <b-col>

          <!-- <h1 class="text-light">Not collected</h1> -->
          <CollectionItem class="unowned" v-bind:weapon_id="img.item_hash" :tooltip_content="['no clan members!']" v-bind:tooltip_title="img.name" v-for="img in resources_collectibles_unowned[0]" :key="img" v-bind:image_url="img.icon_url | bungie_asset"/>
        </b-col>
        <b-col>
          <!-- <h1 class="text-light">Collected</h1> -->
          <CollectionItem v-bind:weapon_id="img.item_hash" v-bind:tooltip_title="img.name" :tooltip_content="img.owners" v-for="img in resources_collectibles[0]" :key="img" v-bind:image_url="img.icon_url | bungie_asset"/>
        </b-col>
      </div>
      <div v-else>
        <CollectionItem v-bind:weapon_id="img.item_hash" v-bind:tooltip_title="img.name" :tooltip_content="img.owners" v-for="img in resources_collectibles[0]" :key="img" v-bind:image_url="img.icon_url | bungie_asset"/>
      </div>
    <!--
    <img v-b-tooltip.hover :title="img.name" v-for="img in resources_collectibles[0]" :src="img.icon_url | bungie_asset" :key="img"/>
    -->
    </b-row>
  </b-container>
</template>

<script>
import $backend from '../backend'
import { error } from 'util';
import CollectionItem from '@/components/CollectionItem.vue'

export default {
  name: 'collectible',
  components: {
    CollectionItem
  },
  data() {
    return {
      loading: false,
      resources_collectibles: [],
      resources_collectibles_unowned: [],
      error: '',
    }
  },
  filters: {
    bungie_asset: function (value) {
      return "https://bungie.net" + value
    }
  },
  methods: {
    fetchDestinyCollectibles() {
      this.loading = true;
      $backend.fetchDestinyCollectibles()
        .then(responseData => {
          this.loading = false;
          this.resources_collectibles.push(responseData)
        }).catch(error => {
          this.error = error.message
        })
    },
    fetchDestinyCollectiblesUnowned() {
      $backend.fetchDestinyCollectiblesUnowned()
        .then(responseData => {
          this.resources_collectibles_unowned.push(responseData);
        }).catch(error => {
          this.error = error.message
        })
    }
  },
  beforeMount() {
    this.fetchDestinyCollectibles();
    this.fetchDestinyCollectiblesUnowned();
  }
}
</script>

<style lang="scss">
.navIndex a {
  color: #9ad3ff;
}

.unowned {
  opacity: 0.5;
}

.p {
  font-family: "nhg display sub";
}

.bg-dark.container-fluid {
  background-color: #0a0a0a !important;
}

.popover-header {
  font-family: "nhg display";
}
</style>
