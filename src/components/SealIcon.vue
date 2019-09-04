<template>
    <img class="iconSeal" :src="getSealIcon" :title="getSealName"/>
</template>

<script>
export default {
  name: 'SealIcon',
  props: { 
    seal: String,
    seals: Array
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
    },
    getSeals: function() {
      // This isn't working because "seals" is an array of seals, and it needs to reference sealDict - and sealDict isn't being referenced here
      var items = Object.keys(this.seals).map(function(key) {
        return [key, this.seals[key]]
      });

      items.sort(function(first, second) {
        return second[1] - first[1];
      });

      return items
    }
  },
  data() {
    return {
      sealDict: {
        'Dredgen': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/59c2c744dca630140a8a01690e0d7fd9.png',
          'displayName': 'Dredgen',
          'difficulty': 2
        },
        'Wayfarer': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/885677894bf02b920ad48bfc60e1bbe2.png',
          'displayName': 'Wayfarer',
          'difficulty': 6
        },
        'Cursebreaker': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/8f755eb3a9109ed7adfc4a8b27871e7a.png',
          'displayName': 'Cursebreaker',
          'difficulty': 7
        },
        'Rivensbane': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/92d4e0eab5d4ab4f29eed35abe6d72d1.png',
          'displayName': 'Rivensbane',
          'difficulty': 3,
        },
        'Reckoner': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/c7d249682178891ed7e737e76e395765.png',
          'displayName': 'Reckoner',
          'difficulty': 4
        },
        'Shadow': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/2e3c60186f7aa64107d843ed697fad1f.png',
          'displayName': 'Shadow',
          'difficulty': 1
        },
        'Blacksmith': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/1a6e93e560351ceb4b5a3bb76504fed6.png',
          'displayName': 'Blacksmith',
          'difficulty': 5,
        },
        'Unbroken': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/d214b107e924ba2d2ac55719d48e0d27.png',
          'displayName': 'Unbroken',
          'difficulty': 9
        },
        'Chronicler': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/f7e108baecc867a8124dc8f6f0bd2b23.png',
          'displayName': 'Chronicler',
          'difficulty': 8
        },
        'MMXIX': {
          'url': 'https://www.bungie.net/common/destiny2_content/icons/c6074edd6d01d703000704ae95461895.png',
          'displayName': 'MMXIX',
          'difficulty': 3
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
  border-color: #0a0a0a !important;
}

.iconSeal {
  display: inline-block;
  height: 30px;
  margin-right: 1px;
  margin-left: 1px
}

</style>
