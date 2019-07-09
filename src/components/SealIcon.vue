<template>
    <img class="iconSeal" :src="getSealIcon" :title="getSealName"/>
</template>

<script>
export default {
  name: 'SealIcon',
  props: { 
    seal: String
  },
  computed: {
    getSealIcon: function() {
      // TODO: Dynamically pull list of seals from the database (via API) so we never have to update this manually again
      if (this.seal) {
        return this.sealDict[this.seal].url
      }
    },
    getSealName: function() {
      if (this.seal) {
        return this.sealDict[this.seal].displayName
      }
    }
  },
  data() {
    return {
      sealDict: {
        'Dredgen': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/59c2c744dca630140a8a01690e0d7fd9.png',
          'displayName': 'Dredgen'
        },
        'Wayfarer': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/885677894bf02b920ad48bfc60e1bbe2.png',
          'displayName': 'Wayfarer'
        },
        'Cursebreaker': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/8f755eb3a9109ed7adfc4a8b27871e7a.png',
          'displayName': 'Cursebreaker'
        },
        'Rivensbane': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/92d4e0eab5d4ab4f29eed35abe6d72d1.png',
          'displayName': 'Rivensbane'
        },
        'Reckoner': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/c7d249682178891ed7e737e76e395765.png',
          'displayName': 'Reckoner'
        },
        'Shadow': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/2e3c60186f7aa64107d843ed697fad1f.png',
          'displayName': 'Shadow'
        },
        'Blacksmith': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/1a6e93e560351ceb4b5a3bb76504fed6.png',
          'displayName': 'Blacksmith'
        },
        'Unbroken': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/d214b107e924ba2d2ac55719d48e0d27.png',
          'displayName': 'Unbroken'
        },
        'Chronicler': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/f7e108baecc867a8124dc8f6f0bd2b23.png',
          'displayName': 'Chronicler'
        }
      }
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

.iconSeal {
  display: inline-block;
  height: 30px;
  margin-right: 1px;
  margin-left: 1px
}

</style>
