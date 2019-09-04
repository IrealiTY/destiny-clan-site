<template>
  <b-container fluid class="bg-dark">
    <img v-bind:src="resources_collectibles[0].icon_url | bungie_asset" />
  </b-container>
</template>

<script>
import $backend from '../backend'
import { error } from 'util';

export default {
  name: 'collectible',
  data() {
    return {
      resources_collectibles: [],
      error: '',
    }
  },
  filters: {
    bungie_asset: function (value) {
      return "https://bungie.net/" + value
    }
  },
  methods: {
    fetchDestinyCollectibles(collectible_hash) {
      $backend.fetchDestinyCollectible(collectible_hash)
        .then(responseData => {
          this.resources_collectibles.push(responseData)
        }).catch(error => {
          this.error = error.message
        })
    }
  },
  beforeMount() {
    this.collectible_hash = '1660030046';
    console.log(this.collectible_hash);
    this.fetchDestinyCollectibles(this.collectible_hash);
  }
}
</script>

<style lang="scss">
.navIndex a {
  color: #9ad3ff;
}
</style>
