TAG=$1

if [ "$TAG" = "" ]; then
   TAG=v0.1.9
fi

git push origin --delete $TAG
git tag -d $TAG
git tag $TAG
git push --tags
